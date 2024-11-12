from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services import scd, od
from framework.conformance import Conformance

RAMIFIES_LABEL = "RAMifies"

def ramify(state: State, model: UUID, prefix = "RAM_") -> UUID:
    bottom = Bottom(state)

    scd_metamodel_id = state.read_dict(state.read_root(), "SCD")
    scd_metamodel = UUID(state.read_value(scd_metamodel_id))

    string_type_id = state.read_dict(state.read_root(), "String")
    string_type = UUID(state.read_value(string_type_id))

    actioncode_type_id = state.read_dict(state.read_root(), "ActionCode")
    actioncode_type = UUID(state.read_value(actioncode_type_id))

    m_scd = scd.SCD(model, state)

    ramified = state.create_node()
    ramified_scd = scd.SCD(ramified, state)

    string_modelref = ramified_scd.create_model_ref("String", string_type)
    actioncode_modelref = ramified_scd.create_model_ref("ActionCode", actioncode_type)

    already_ramified = set() # for correct order of ramification

    classes = m_scd.get_classes()
    for class_name, class_node in classes.items():
        # For every class in our original model, create a class:
        #   - abstract: False
        #   - min-card: 0
        #   - max-card: same as original
        upper_card = od.find_cardinality(bottom, class_node, od.get_scd_mm_class_uppercard_node(bottom))
        # print('creating class', class_name, "with card 0 ..", upper_card)
        ramified_class = ramified_scd.create_class(prefix+class_name, abstract=None, max_c=upper_card)
        # traceability link
        bottom.create_edge(ramified_class, class_node, RAMIFIES_LABEL)

        # We don't add a 'label' attribute (as described in literature on RAMification)
        # Instead, the names of the objects (which only exist in the scope of the object diagram 'model', and are not visible to the matcher) are used as labels

        for (attr_name, attr_edge) in od.get_attributes(bottom, class_node):
            # print('  creating attribute', attr_name, "with type String")
            # Every attribute becomes 'string' type
            # The string will be a Python expression
            ramified_attr_link = ramified_scd._create_attribute_link(prefix+class_name, actioncode_modelref, prefix+attr_name, optional=True)
            # create traceability link
            bottom.create_edge(ramified_attr_link, attr_edge, RAMIFIES_LABEL)

        # Additional condition that can be specified
        # In LHS, this will be a boolean expression (pre-condition)
        # In RHS, this is just a piece of action code
        ramified_scd._create_attribute_link(prefix+class_name, actioncode_modelref, "condition", optional=True)

        already_ramified.add(class_name)

    glob_cond = ramified_scd.create_class("GlobalCondition", abstract=None)
    ramified_scd._create_attribute_link("GlobalCondition", actioncode_modelref, "condition", optional=False)

    assocs_to_ramify = m_scd.get_associations()

    while len(assocs_to_ramify) > 0:
        ramify_later = {}
        for assoc_name, assoc_node in assocs_to_ramify.items():
            # For every association in our original model, create an association:
            #   - src-min-card: 0
            #   - src-max-card: same as original
            #   - tgt-min-card: 0
            #   - tgt-max-card: same as original

            if assoc_name in already_ramified:
                raise Exception("Assertion failed: did not expect this to ever happen!")
                continue

            _, src_upper_card, _, tgt_upper_card = m_scd.get_assoc_cardinalities(assoc_node)
            src = m_scd.get_class_name(bottom.read_edge_source(assoc_node))
            tgt = m_scd.get_class_name(bottom.read_edge_target(assoc_node))

            if src not in already_ramified or tgt not in already_ramified:
                ramify_later[assoc_name] = assoc_node
                continue

            # print('creating assoc', src, "->", tgt, ", name =", assoc_name, ", src card = 0 ..", src_upper_card, "and tgt card = 0 ..", tgt_upper_card)

            ramified_assoc = ramified_scd.create_association(name=prefix+assoc_name,
                source=prefix+src, target=prefix+tgt,
                src_max_c=src_upper_card,
                tgt_max_c=tgt_upper_card)

            # create traceability link
            bottom.create_edge(ramified_assoc, assoc_node, RAMIFIES_LABEL)

            # Additional constraint that can be specified
            ramified_scd._create_attribute_link(prefix+assoc_name, actioncode_modelref, "condition", optional=True)

            already_ramified.add(assoc_name)

            # Associations can also have attributes...
            for (attr_name, attr_edge) in od.get_attributes(bottom, assoc_node):
                # print('  creating attribute', attr_name, "with type String")
                # Every attribute becomes 'string' type
                # The string will be a Python expression
                ramified_attr_link = ramified_scd._create_attribute_link(prefix+assoc_name, actioncode_modelref, prefix+attr_name, optional=True)
                # create traceability link
                bottom.create_edge(ramified_attr_link, attr_edge, RAMIFIES_LABEL)


        assocs_to_ramify = ramify_later

    for inh_name, inh_node in m_scd.get_inheritances().items():
        # Re-create inheritance links like in our original model:
        src = m_scd.get_class_name(bottom.read_edge_source(inh_node))
        tgt = m_scd.get_class_name(bottom.read_edge_target(inh_node))
        # print('creating inheritance link', prefix+src, '->', prefix+tgt)
        ramified_inh_link = ramified_scd.create_inheritance(prefix+src, prefix+tgt)

    # Double-check: The RAMified meta-model should also conform to 'SCD':
    conf = Conformance(state, ramified, scd_metamodel)
    if len(conf.check_nominal(log=True)) > 0:
        raise Exception("Unexpected error: RAMified MM does not conform to SCD MM")

    return ramified

# Every RAMified type has a link to its original type
def get_original_type(bottom, typ: UUID):
    original_types = bottom.read_outgoing_elements(typ, RAMIFIES_LABEL)
    if len(original_types) > 1:
        raise Exception("Expected at most 1 original type, got " + str(len(original_types)))
    elif len(original_types) == 1:
        return original_types[0]
