# Things you can do:
#   - Create/delete objects, associations, attributes
#   - Change attribute values
#   - ? that's it?

import re
from uuid import UUID
from api.od import ODAPI, bind_api
from services.bottom.V0 import Bottom
from transformation import ramify
from services import od
from services.primitives.string_type import String
from services.primitives.actioncode_type import ActionCode
from services.primitives.integer_type import Integer
from util.eval import exec_then_eval, simply_exec

identifier_regex_pattern = '[_A-Za-z][._A-Za-z0-9]*'
identifier_regex = re.compile(identifier_regex_pattern)

class TryAgainNextRound(Exception):
    pass

# Rewrite is performed in-place (modifying `host_m`)
def rewrite(state,
    rhs_m: UUID, # RHS-pattern
    pattern_mm: UUID, # meta-model of both patterns (typically the RAMified host_mm)
    lhs_match: dict, # a match, morphism, from lhs_m to host_m (mapping pattern name -> host name), typically found by the 'match_od'-function.
    host_m: UUID, # host model
    host_mm: UUID, # host meta-model
    eval_context={}, # optional: additional variables/functions to be available while executing condition-code. These will be seen as global variables.
):
    bottom = Bottom(state)

    # Need to come up with a new, unique name when creating new element in host-model:
    def first_available_name(suggested_name: str):
        if len(bottom.read_outgoing_elements(host_m, suggested_name)) == 0:
            return suggested_name # already unique :)
        i = 0
        while True:
            name = suggested_name + str(i)
            if len(bottom.read_outgoing_elements(host_m, name)) == 0:
                return name # found unique name
            i += 1

    # function that can be called from within RHS action code
    def matched_callback(pattern_name: str):
        host_name = lhs_match[pattern_name]
        return bottom.read_outgoing_elements(host_m, host_name)[0]

    scd_metamodel_id = state.read_dict(state.read_root(), "SCD")
    scd_metamodel = UUID(state.read_value(scd_metamodel_id))

    class_type = od.get_scd_mm_class_node(bottom)
    attr_link_type = od.get_scd_mm_attributelink_node(bottom)
    assoc_type = od.get_scd_mm_assoc_node(bottom)
    actioncode_type = od.get_scd_mm_actioncode_node(bottom)
    modelref_type = od.get_scd_mm_modelref_node(bottom)

    # To be replaced by ODAPI (below)
    host_od = od.OD(host_mm, host_m, bottom.state)
    rhs_od = od.OD(pattern_mm, rhs_m, bottom.state)

    host_odapi = ODAPI(state, host_m, host_mm)
    host_mm_odapi = ODAPI(state, host_mm, scd_metamodel)
    rhs_odapi = ODAPI(state, rhs_m, pattern_mm)
    rhs_mm_odapi = ODAPI(state, pattern_mm, scd_metamodel)

    lhs_keys = lhs_match.keys()
    rhs_keys = set(k for k in bottom.read_keys(rhs_m)
        # extremely dirty - should think of a better way
        if "GlobalCondition" not in k and not k.endswith("_condition") and not k.endswith(".condition")
        and (not k.endswith("_name") or k.endswith("RAM_name")) and (not k.endswith(".name")))

    # See which keys were ignored by the rewriter:
    # print('filtered out:', set(k for k in bottom.read_keys(rhs_m) if k.endswith(".name") or k.endswith("_name")))

    common = lhs_keys & rhs_keys
    to_delete = lhs_keys - common
    to_create = rhs_keys - common

    # print("to delete:", to_delete)
    # print("to create:", to_create)

    # to be grown
    rhs_match = { name : lhs_match[name] for name in common }


    bound_api = bind_api(host_odapi)
    original_delete = bound_api["delete"]
    def wrapped_delete(obj):
        not_allowed_to_delete = { host_odapi.get(host_name): pattern_name  for pattern_name, host_name in rhs_match.items() }
        if obj in not_allowed_to_delete:
            pattern_name = not_allowed_to_delete[obj]
            raise Exception(f"\n\nYou're trying to delete the element that was matched with the RHS-element '{pattern_name}'. This is not allowed! You're allowed to delete anything BUT NOT elements matched with your RHS-pattern. Instead, simply remove the element '{pattern_name}' from your RHS, if you want to delete it.")
        return original_delete(obj)
    bound_api["delete"] = wrapped_delete
    builtin = {
        **bound_api,
        'matched': matched_callback,
        'odapi': host_odapi,
    }
    for key in eval_context:
        if key in builtin:
            print(f"WARNING: custom global '{key}' overrides pre-defined API function. Consider renaming it.")
    eval_globals = {
        **builtin,
        **eval_context,
    }

    # 1. Perform creations - in the right order!
    remaining_to_create = list(to_create)
    while len(remaining_to_create) > 0:
        next_round = []
        for rhs_name in remaining_to_create:
            # Determine the type of the thing to create
            rhs_obj = rhs_odapi.get(rhs_name)
            # what to name our new object?
            try:
                name_expr = rhs_odapi.get_slot_value(rhs_obj, "name")
            except:
                name_expr = f'"{rhs_name}"' # <- if the 'name' slot doesnt exist, use the pattern element name
            suggested_name = exec_then_eval(name_expr, _globals=eval_globals)
            if not identifier_regex.match(suggested_name):
                raise Exception(f"In the RHS pattern element '{rhs_name}', the following name-expression:\n  {name_expr}\nproduced the name:\n  '{suggested_name}'\nwhich contains illegal characters.\nNames should match the following regex: {identifier_regex_pattern}")
            rhs_type = rhs_odapi.get_type(rhs_obj)
            host_type = ramify.get_original_type(bottom, rhs_type)
            # for debugging:
            if host_type != None:
                host_type_name = host_odapi.get_name(host_type)
            else:
                host_type_name = ""

            def get_src_tgt():
                src = rhs_odapi.get_source(rhs_obj)
                tgt = rhs_odapi.get_target(rhs_obj)
                src_name = rhs_odapi.get_name(src)
                tgt_name = rhs_odapi.get_name(tgt)
                try:
                    host_src_name = rhs_match[src_name]
                    host_tgt_name = rhs_match[tgt_name]
                except KeyError:
                    # some creations (e.g., edges) depend on other creations
                    raise TryAgainNextRound()
                host_src = host_odapi.get(host_src_name)
                host_tgt = host_odapi.get(host_tgt_name)
                return (host_src_name, host_tgt_name, host_src, host_tgt)

            try:
                if od.is_typed_by(bottom, rhs_type, class_type):
                    obj_name = first_available_name(suggested_name)
                    host_od._create_object(obj_name, host_type)
                    host_odapi._ODAPI__recompute_mappings()
                    rhs_match[rhs_name] = obj_name
                elif od.is_typed_by(bottom, rhs_type, assoc_type):
                    _, _, host_src, host_tgt = get_src_tgt()
                    link_name = first_available_name(suggested_name)
                    host_od._create_link(link_name, host_type, host_src, host_tgt)
                    host_odapi._ODAPI__recompute_mappings()
                    rhs_match[rhs_name] = link_name
                elif od.is_typed_by(bottom, rhs_type, attr_link_type):
                    host_src_name, _, host_src, host_tgt = get_src_tgt()
                    host_attr_link = ramify.get_original_type(bottom, rhs_type)
                    host_attr_name = host_mm_odapi.get_slot_value(host_attr_link, "name")
                    link_name = f"{host_src_name}_{host_attr_name}" # must follow naming convention here
                    host_od._create_link(link_name, host_type, host_src, host_tgt)
                    host_odapi._ODAPI__recompute_mappings()
                    rhs_match[rhs_name] = link_name
                elif rhs_type == rhs_mm_odapi.get("ActionCode"):
                    # If we encounter ActionCode in our RHS, we assume that the code computes the value of an attribute...
                    # This will be the *value* of an attribute. The attribute-link (connecting an object to the attribute) will be created as an edge later.

                    # Problem: attributes must follow the naming pattern '<obj_name>.<attr_name>'
                    # So we must know the host-object-name, and the host-attribute-name.
                    # However, all we have access to here is the name of the attribute in the RHS.
                    # We cannot even see the link to the RHS-object.
                    # But, assuming the RHS-attribute is also named '<RAMified_obj_name>.<RAMified_attr_name>', we can:
                    rhs_src_name, rhs_attr_name = rhs_name.split('.')
                    try:
                        host_src_name = rhs_match[rhs_src_name]
                    except KeyError:
                        # unmet dependency - object to which attribute belongs not created yet
                        raise TryAgainNextRound()
                    rhs_src_type = rhs_odapi.get_type(rhs_odapi.get(rhs_src_name))
                    rhs_src_type_name = rhs_mm_odapi.get_name(rhs_src_type)
                    rhs_attr_link_name = f"{rhs_src_type_name}_{rhs_attr_name}"
                    rhs_attr_link = rhs_mm_odapi.get(rhs_attr_link_name)
                    host_attr_link = ramify.get_original_type(bottom, rhs_attr_link)
                    host_attr_name = host_mm_odapi.get_slot_value(host_attr_link, "name")
                    val_name = f"{host_src_name}.{host_attr_name}"
                    python_expr = ActionCode(UUID(bottom.read_value(rhs_obj)), bottom.state).read()
                    result = exec_then_eval(python_expr, _globals=eval_globals)
                    host_odapi.create_primitive_value(val_name, result, is_code=False)
                    rhs_match[rhs_name] = val_name
                else:
                    rhs_type_name = rhs_odapi.get_name(rhs_type)
                    raise Exception(f"Host type {host_type_name} of pattern element '{rhs_name}:{rhs_type_name}' is not a class, association or attribute link. Don't know what to do with it :(")
            except TryAgainNextRound:
                next_round.append(rhs_name)

        if len(next_round) == len(remaining_to_create):
            raise Exception("Creation of objects did not make any progress - there must be some kind of cyclic dependency?!")

        remaining_to_create = next_round

    # 2. Perform updates (only on values)
    for common_name in common:
        host_obj_name = rhs_match[common_name]
        host_obj = host_odapi.get(host_obj_name)
        host_type = host_odapi.get_type(host_obj)
        if od.is_typed_by(bottom, host_type, class_type):
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, assoc_type):
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, attr_link_type):
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, modelref_type):
            rhs_obj = rhs_odapi.get(common_name)
            python_expr = ActionCode(UUID(bottom.read_value(rhs_obj)), bottom.state).read()
            result = exec_then_eval(python_expr,
                _globals=eval_globals,
                _locals={'this': host_obj}) # 'this' can be used to read the previous value of the slot
            host_odapi.overwrite_primitive_value(host_obj_name, result, is_code=False)
        else:
            msg = f"Don't know what to do with element '{common_name}' -> '{host_obj_name}:{host_type}')"
            # print(msg)
            raise Exception(msg)

    # 3. Perform deletions
    # This way, action code can read from elements that are deleted...
    # Even better would be to not modify the model in-place, but use copy-on-write...
    for pattern_name_to_delete in to_delete:
        # For every name in `to_delete`, look up the name of the matched element in the host graph
        model_el_name_to_delete = lhs_match[pattern_name_to_delete]
        # print('deleting', model_el_name_to_delete)
        # Look up the matched element in the host graph
        els_to_delete = bottom.read_outgoing_elements(host_m, model_el_name_to_delete)
        if len(els_to_delete) == 0:
            # This can happen: if the SRC/TGT of a link was deleted, the link itself is also immediately deleted.
            # If we then try to delete the link, it is not found (already gone).
            # The most accurate way of handling this, would be to perform deletions in opposite order of creations (see the whole TryNextRound-mechanism above)
            # However I *think* it is also OK to simply ignore this case.
            pass
        elif len(els_to_delete) == 1:
            bottom.delete_element(els_to_delete[0])
        else:
            raise Exception("This should never happen!")

    # 4. Object-level actions
    # Iterate over the (now complete) mapping RHS -> Host
    for rhs_name, host_name in rhs_match.items():
        host_obj = host_odapi.get(host_name)
        rhs_obj = rhs_odapi.get(rhs_name)
        rhs_type = rhs_odapi.get_type(rhs_obj)
        rhs_type_of_type = rhs_mm_odapi.get_type(rhs_type)
        rhs_type_of_type_name = rhs_mm_odapi.get_name(rhs_type_of_type)
        if rhs_mm_odapi.cdapi.is_subtype(super_type_name="Class", sub_type_name=rhs_type_of_type_name):
            # rhs_obj is an object or link (because association is subtype of class)
            python_code = rhs_odapi.get_slot_value_default(rhs_obj, "condition", default="")
            simply_exec(python_code,
                _globals=eval_globals,
                _locals={'this': host_obj})

    # 5. Execute global actions
    for cond_name, cond in rhs_odapi.get_all_instances("GlobalCondition"):
        python_code = rhs_odapi.get_slot_value(cond, "condition")
        simply_exec(python_code, _globals=eval_globals)

    return rhs_match