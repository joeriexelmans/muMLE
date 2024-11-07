# Things you can do:
#   - Create/delete objects, associations, attributes
#   - Change attribute values
#   - ? that's it?

from uuid import UUID
from api.od import ODAPI, bind_api
from services.bottom.V0 import Bottom
from transformation import ramify
from services import od
from services.primitives.string_type import String
from services.primitives.actioncode_type import ActionCode
from services.primitives.integer_type import Integer
from util.eval import exec_then_eval, simply_exec

def preprocess_rule(state, lhs: UUID, rhs: UUID, name_mapping):
    bottom = Bottom(state)

    to_delete = { name for name in bottom.read_keys(lhs) if name not in bottom.read_keys(rhs) and name in name_mapping }
    to_create = { name for name in bottom.read_keys(rhs) if name not in bottom.read_keys(lhs)
        # extremely dirty:
        and "GlobalCondition" not in name }
    common = { name for name in bottom.read_keys(lhs) if name in bottom.read_keys(rhs) and name in name_mapping }

    print("to_delete:", to_delete)
    print("to_create:", to_create)

    return to_delete, to_create, common

# Rewrite is performed in-place (modifying `host_m`)
# Also updates the `mapping` in-place, to become RHS -> host
def rewrite(state, lhs_m: UUID, rhs_m: UUID, pattern_mm: UUID, name_mapping: dict, host_m: UUID, host_mm: UUID):
    bottom = Bottom(state)

    orig_name_mapping = dict(name_mapping)

    # function that can be called from within RHS action code
    def matched_callback(pattern_name: str):
        host_name = orig_name_mapping[pattern_name]
        return bottom.read_outgoing_elements(host_m, host_name)[0]

    scd_metamodel_id = state.read_dict(state.read_root(), "SCD")
    scd_metamodel = UUID(state.read_value(scd_metamodel_id))

    class_type = od.get_scd_mm_class_node(bottom)
    attr_link_type = od.get_scd_mm_attributelink_node(bottom)
    assoc_type = od.get_scd_mm_assoc_node(bottom)
    modelref_type = od.get_scd_mm_modelref_node(bottom)

    m_od = od.OD(host_mm, host_m, bottom.state)
    rhs_od = od.OD(pattern_mm, rhs_m, bottom.state)

    to_delete, to_create, common = preprocess_rule(state, lhs_m, rhs_m, orig_name_mapping)

    odapi = ODAPI(state, host_m, host_mm)

    # Perform deletions
    for pattern_name_to_delete in to_delete:
        # For every name in `to_delete`, look up the name of the matched element in the host graph
        model_el_name_to_delete = name_mapping[pattern_name_to_delete]
        # print('deleting', model_el_name_to_delete)
        # Look up the matched element in the host graph
        el_to_delete, = bottom.read_outgoing_elements(host_m, model_el_name_to_delete)
        # Delete
        bottom.delete_element(el_to_delete)
        # Remove from mapping
        del name_mapping[pattern_name_to_delete]

    # extended_mapping = dict(name_mapping) # will be extended with created elements
    edges_to_create = [] # postpone creation of edges after creation of nodes

    # Perform creations
    for pattern_name_to_create in to_create:
        # print('creating', pattern_name_to_create)
        # We have to come up with a name for the element-to-create in the host graph
        i = 0
        while True:
            model_el_name_to_create = pattern_name_to_create + str(i) # use the label of the element in the RHS as a basis
            if len(bottom.read_outgoing_elements(host_m, model_el_name_to_create)) == 0:
                break # found an available name
            i += 1
        
        # Determine the type of the thing to create
        rhs_el_to_create, = bottom.read_outgoing_elements(rhs_m, pattern_name_to_create)
        rhs_type = od.get_type(bottom, rhs_el_to_create)
        original_type = ramify.get_original_type(bottom, rhs_type)
        if original_type != None:
            # Now get the type of the type
            if od.is_typed_by(bottom, original_type, class_type):
                # It's type is typed by Class -> it's an object
                # print(' -> creating object')
                o = m_od._create_object(model_el_name_to_create, original_type)
                name_mapping[pattern_name_to_create] = model_el_name_to_create
            elif od.is_typed_by(bottom, original_type, attr_link_type):
                # print(' -> postpone (is attribute link)')
                edges_to_create.append((pattern_name_to_create, rhs_el_to_create, original_type, 'attribute link', model_el_name_to_create))
            elif od.is_typed_by(bottom, original_type, assoc_type):
                # print(' -> postpone (is link)')
                edges_to_create.append((pattern_name_to_create, rhs_el_to_create, original_type, 'link', model_el_name_to_create))
            else:
                original_type_name = od.get_object_name(bottom, host_mm, original_type)
                print(" -> warning: don't know about", original_type_name)
        else:
            # print(" -> no original (un-RAMified) type")
            # assume the type of the object is already the original type
            # this is because primitive types (e.g., Integer) are not RAMified
            type_name = od.get_object_name(bottom, pattern_mm, rhs_type)
            if type_name == "ActionCode":
                # Assume the string is a Python expression to evaluate
                python_expr = ActionCode(UUID(bottom.read_value(rhs_el_to_create)), bottom.state).read()

                result = exec_then_eval(python_expr, _globals={
                    **bind_api(odapi),
                    'matched': matched_callback,
                })

                # Write the result into the host model.
                # This will be the *value* of an attribute. The attribute-link (connecting an object to the attribute) will be created as an edge later.
                if isinstance(result, int):
                    m_od.create_integer_value(model_el_name_to_create, result)
                elif isinstance(result, str):
                    m_od.create_string_value(model_el_name_to_create, result)
                name_mapping[pattern_name_to_create] = model_el_name_to_create
            else:
                msg = f"RHS element '{pattern_name_to_create}' needs to be created in host, but has no un-RAMified type, and I don't know what to do with it. It's type is '{type_name}'"
                raise Exception(msg)

    # print("create edges....")
    for pattern_name_to_create, rhs_el_to_create, original_type, original_type_name, model_el_name_to_create in edges_to_create:
        # print('creating', pattern_name_to_create)
        if original_type_name == 'attribute link':
            # print(' -> creating attribute link')
            src = bottom.read_edge_source(rhs_el_to_create)
            src_name = od.get_object_name(bottom, rhs_m, src)
            tgt = bottom.read_edge_target(rhs_el_to_create)
            tgt_name = od.get_object_name(bottom, rhs_m, tgt)
            obj_name = name_mapping[src_name] # name of object in host graph to create slot for
            orig_attr_name = od.get_attr_name(bottom, original_type)
            m_od.create_slot(orig_attr_name, obj_name, name_mapping[tgt_name])
        elif original_type_name == 'link':
            # print(' -> creating link')
            src = bottom.read_edge_source(rhs_el_to_create)
            src_name = od.get_object_name(bottom, rhs_m, src)
            tgt = bottom.read_edge_target(rhs_el_to_create)
            tgt_name = od.get_object_name(bottom, rhs_m, tgt)
            obj_name = name_mapping[src_name] # name of object in host graph to create slot for
            attr_name = od.get_object_name(bottom, host_mm, original_type)
            m_od.create_link(model_el_name_to_create, attr_name, obj_name, name_mapping[tgt_name])


    # Perform updates (only on values)
    for pattern_el_name in common:
        host_el_name = name_mapping[pattern_el_name]
        host_el, = bottom.read_outgoing_elements(host_m, host_el_name)
        # print('updating', host_el_name, host_el)
        host_type = od.get_type(bottom, host_el)
        # print('we have', pattern_el_name, '->', host_el_name, 'of type', type_name)
        if od.is_typed_by(bottom, host_type, class_type):
            # print(' -> is classs')
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, assoc_type):
            # print(' -> is association')
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, attr_link_type):
            # print(' -> is attr link')
            # nothing to do
            pass
        elif od.is_typed_by(bottom, host_type, modelref_type):
            # print(' -> is modelref')
            old_value, _ = od.read_primitive_value(bottom, host_el, host_mm)
            rhs_el, = bottom.read_outgoing_elements(rhs_m, pattern_el_name)
            python_expr, _ = od.read_primitive_value(bottom, rhs_el, pattern_mm)
            result = exec_then_eval(python_expr,
                _globals={
                    **bind_api(odapi),
                    'matched': matched_callback,
                },
                _locals={'this': host_el})
            # print('eval result=', result)
            if isinstance(result, int):
                # overwrite the old value, in-place
                referred_model_id = UUID(bottom.read_value(host_el))
                Integer(referred_model_id, state).create(result)
            else:
                raise Exception("Unimplemented type. Value:", result)
        else:
            msg = f"Don't know what to do with element '{pattern_el_name}'->'{host_el_name}' of type ({host_type})"
            # print(msg)
            raise Exception(msg)

    rhs_odapi = ODAPI(state, rhs_m, pattern_mm)
    for cond_name, cond in rhs_odapi.get_all_instances("GlobalCondition"):
        python_code = rhs_odapi.get_slot_value(cond, "condition")
        simply_exec(python_code, _globals={
            **bind_api(odapi),
            'matched': matched_callback,
        })
