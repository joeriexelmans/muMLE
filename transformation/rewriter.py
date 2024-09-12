# Things you can do:
#   - Create/delete objects, associations, attributes
#   - Change attribute values
#   - ? that's it?

from uuid import UUID
from services.bottom.V0 import Bottom
from transformation import ramify
from services import od
from services.primitives.string_type import String
from services.primitives.integer_type import Integer

def process_rule(state, lhs: UUID, rhs: UUID):
    bottom = Bottom(state)

    # : bottom.read_outgoing_elements(rhs, name)[0]
    to_delete = { name for name in bottom.read_keys(lhs) if name not in bottom.read_keys(rhs) }
    to_create = { name for name in bottom.read_keys(rhs) if name not in bottom.read_keys(lhs) }
    common = { name for name in bottom.read_keys(lhs) if name in bottom.read_keys(rhs) }

    print("to_delete:", to_delete)
    print("to_create:", to_create)

    return to_delete, to_create, common

def rewrite(state, lhs: UUID, rhs: UUID, rhs_mm: UUID, match_mapping: dict, m_to_transform: UUID, mm: UUID) -> UUID:
    bottom = Bottom(state)

    scd_metamodel_id = state.read_dict(state.read_root(), "SCD")
    scd_metamodel = UUID(state.read_value(scd_metamodel_id))

    class_type = od.get_scd_mm_class_node(bottom)
    attr_link_type = od.get_scd_mm_attributelink_node(bottom)
    assoc_type = od.get_scd_mm_assoc_node(bottom)
    modelref_type = od.get_scd_mm_modelref_node(bottom)

    m_od = od.OD(mm, m_to_transform, bottom.state)
    rhs_od = od.OD(rhs_mm, rhs, bottom.state)

    print('rhs type:', od.get_type(bottom, rhs))

    to_delete, to_create, common = process_rule(state, lhs, rhs)

    # Perform deletions
    for pattern_name_to_delete in to_delete:
        # For every name in `to_delete`, look up the name of the matched element in the host graph
        model_element_name_to_delete = match_mapping[pattern_name_to_delete]
        print('deleting', model_element_name_to_delete)
        # Look up the matched element in the host graph
        element_to_delete, = bottom.read_outgoing_elements(m_to_transform, model_element_name_to_delete)
        # Delete
        bottom.delete_element(element_to_delete)

    extended_mapping = dict(match_mapping) # will be extended with created elements
    edges_to_create = [] # postpone creation of edges after creation of nodes

    # Perform creations
    for pattern_name_to_create in to_create:
        print('creating', pattern_name_to_create)
        # We have to come up with a name for the element-to-create in the host graph
        i = 0
        while True:
            model_element_name_to_create = pattern_name_to_create + str(i) # use the label of the element in the RHS as a basis
            if len(bottom.read_outgoing_elements(m_to_transform, model_element_name_to_create)) == 0:
                break # found an available name
        
        # Determine the type of the thing to create
        rhs_element_to_create, = bottom.read_outgoing_elements(rhs, pattern_name_to_create)
        rhs_type = od.get_type(bottom, rhs_element_to_create)
        original_type = ramify.get_original_type(bottom, rhs_type)
        if original_type != None:
            # Now get the type of the type
            if od.is_typed_by(bottom, original_type, class_type):
                # It's type is typed by Class -> it's an object
                print(' -> creating object')
                o = m_od._create_object(model_element_name_to_create, original_type)
                extended_mapping[pattern_name_to_create] = model_element_name_to_create
            elif od.is_typed_by(bottom, original_type, attr_link_type):
                print(' -> postpone (is attribute link)')
                edges_to_create.append((pattern_name_to_create, rhs_element_to_create, original_type, 'attribute link', rhs_type, model_element_name_to_create))
            elif od.is_typed_by(bottom, original_type, assoc_type):
                print(' -> postpone (is link)')
                edges_to_create.append((pattern_name_to_create, rhs_element_to_create, original_type, 'link', rhs_type, model_element_name_to_create))
            else:
                original_type_name = od.get_object_name(bottom, mm, original_type)
                print(" -> warning: don't know about", original_type_name)
        else:
            print(" -> no original (un-RAMified) type")
            # assume the type of the object is already the original type
            # this is because primitive types (e.g., Integer) are not RAMified
            type_name = od.get_object_name(bottom, rhs_mm, rhs_type)
            if type_name == "String":
                s_model = UUID(bottom.read_value(rhs_element_to_create))
                python_expr = String(s_model, bottom.state).read()
                result = eval(python_expr, {}, {})
                print('result:', result)
                if isinstance(result, int):
                    m_od.create_integer_value(model_element_name_to_create, result)
                elif isinstance(result, str):
                    m_od.create_string_value(model_element_name_to_create, result)
                extended_mapping[pattern_name_to_create] = model_element_name_to_create


    print('extended_mapping:', extended_mapping)

    print("create edges....")
    for pattern_name_to_create, rhs_element_to_create, original_type, original_type_name, rhs_type, model_element_name_to_create in edges_to_create:
        print('creating', pattern_name_to_create)
        if original_type_name == 'attribute link':
            print(' -> creating attribute link')
            src = bottom.read_edge_source(rhs_element_to_create)
            src_name = od.get_object_name(bottom, rhs, src)
            tgt = bottom.read_edge_target(rhs_element_to_create)
            tgt_name = od.get_object_name(bottom, rhs, tgt)
            obj_name = extended_mapping[src_name] # name of object in host graph to create slot for
            attr_name = od.get_object_name(bottom, mm, original_type)
            class_name = m_od.get_class_of_object(obj_name)
            # Just when you thought the code couldn't get any dirtier:
            attribute_name = attr_name[len(class_name)+1:]
            # print(attribute_name, obj_name, extended_mapping[tgt_name])
            m_od.create_slot(attribute_name, obj_name, extended_mapping[tgt_name])
        elif original_type_name == 'link':
            print(' -> creating link')
            src = bottom.read_edge_source(rhs_element_to_create)
            src_name = od.get_object_name(bottom, rhs, src)
            tgt = bottom.read_edge_target(rhs_element_to_create)
            tgt_name = od.get_object_name(bottom, rhs, tgt)
            obj_name = extended_mapping[src_name] # name of object in host graph to create slot for
            attr_name = od.get_object_name(bottom, mm, original_type)
            class_name = m_od.get_class_of_object(obj_name)
            # print(attr_name, obj_name, extended_mapping[tgt_name])
            m_od.create_link(model_element_name_to_create, attr_name, obj_name, extended_mapping[tgt_name])

    # Perform updates
    for pattern_element_name in common:
        model_element_name = match_mapping[pattern_element_name]
        print('updating', model_element_name)
        model_element, = bottom.read_outgoing_elements(m_to_transform, model_element_name)
        old_value = bottom.read_value(model_element)
        print('old value:', old_value)
        host_type = od.get_type(bottom, model_element)
        if od.is_typed_by(bottom, host_type, class_type):
            print(' -> is classs')
        elif od.is_typed_by(bottom, host_type, attr_link_type):
            print(' -> is attr link')
        elif od.is_typed_by(bottom, host_type, modelref_type):
            print(' -> is modelref')
            referred_model_id = UUID(bottom.read_value(model_element))
            # referred_model_type = od.get_type(bottom, referred_model_id) # None
            # print('referred_model_type:', referred_model_type)

            host_type_name = od.get_object_name(bottom, mm, host_type)
            print('host_type_name:', host_type_name)
            if host_type_name == "Integer":
                v = Integer(UUID(old_value), state).read()
            elif host_type_name == "String":
                v = String(UUID(old_value), state).read()
            else:
                raise Exception("Unimplemented type:", host_type_name)

            # the referred model itself doesn't have a type, so we have to look at the type of the ModelRef element in the RHS-MM:
            rhs_element, = bottom.read_outgoing_elements(rhs, pattern_element_name)
            rhs_type = od.get_type(bottom, rhs_element)
            rhs_type_name = od.get_object_name(bottom, rhs_mm, rhs_type)
            print("rhs_type_name:", rhs_type_name)

            print(od.get_object_name(bottom, mm, model_element))

            if rhs_type_name == "String":
                python_expr = String(UUID(bottom.read_value(rhs_element)), state).read()
                result = eval(python_expr, {}, {'v': v})
                print('eval result=', result)
                if isinstance(result, int):
                    # overwrite the old value
                    Integer(UUID(old_value), state).create(result)
                else:
                    raise Exception("Unimplemented type. Value:", result)
