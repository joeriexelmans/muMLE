from state.base import State, UUID
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from services.primitives.actioncode_type import ActionCode


def bootstrap_type(type_name: str, scd_root: UUID, model_root: UUID, state: State):
    bottom = Bottom(state)
    # create class
    type_class_node = bottom.create_node()  # create class node
    bottom.create_edge(model_root, type_class_node, type_name)  # attach to model
    class_class_node, = bottom.read_outgoing_elements(scd_root, "Class")  # retrieve type
    bottom.create_edge(type_class_node, class_class_node, "Morphism")  # create morphism link
    scd_int_node, = bottom.read_outgoing_elements(scd_root, "Integer")
    # set min_cardinality
    min_c_model = bottom.create_node()
    Integer(min_c_model, state).create(1)
    min_c_node = bottom.create_node(str(min_c_model))
    bottom.create_edge(model_root, min_c_node, f"{type_name}.lower_cardinality")
    min_c_link = bottom.create_edge(type_class_node, min_c_node)
    bottom.create_edge(model_root, min_c_link, f"{type_name}_lower_cardinality")
    scd_link, = bottom.read_outgoing_elements(scd_root, "Class_lower_cardinality")
    bottom.create_edge(min_c_node, scd_int_node, "Morphism")
    bottom.create_edge(min_c_link, scd_link, "Morphism")
    # set max_cardinality
    max_c_model = bottom.create_node()
    Integer(max_c_model, state).create(1)
    max_c_node = bottom.create_node(str(max_c_model))
    bottom.create_edge(model_root, max_c_node, f"{type_name}.upper_cardinality")
    max_c_link = bottom.create_edge(type_class_node, max_c_node)
    bottom.create_edge(model_root, max_c_link, f"{type_name}_upper_cardinality")
    scd_link, = bottom.read_outgoing_elements(scd_root, "Class_upper_cardinality")
    bottom.create_edge(max_c_node, scd_int_node, "Morphism")
    bottom.create_edge(max_c_link, scd_link, "Morphism")
    return type_class_node

def bootstrap_constraint(class_node, type_name: str, python_type: str, scd_root: UUID, model_root: UUID, actioncode_type: UUID, state: State):
    bottom = Bottom(state)
    constraint_model = bottom.create_node()
    ActionCode(constraint_model, state).create(f"isinstance(read_value(this),{python_type})")
    constraint_node = bottom.create_node(str(constraint_model))
    bottom.create_edge(model_root, constraint_node, f"{type_name}.constraint")
    constraint_link = bottom.create_edge(class_node, constraint_node)
    bottom.create_edge(model_root, constraint_link, f"{type_name}_constraint")
    scd_node = actioncode_type
    scd_link, = bottom.read_outgoing_elements(scd_root, "Element_constraint")
    bottom.create_edge(constraint_node, scd_node, "Morphism")
    bottom.create_edge(constraint_link, scd_link, "Morphism")
    
def bootstrap_primitive_types(scd_root, state, integer_type, boolean_type, float_type, string_type, type_type, actioncode_type, bytes_type):
    # Order is important: Integer must come first
    class_integer    = bootstrap_type("Integer",    scd_root, integer_type,    state)
    class_type       = bootstrap_type("Type",       scd_root, type_type,       state)
    class_boolean    = bootstrap_type("Boolean",    scd_root, boolean_type,    state)
    class_float      = bootstrap_type("Float",      scd_root, float_type,      state)
    class_string     = bootstrap_type("String",     scd_root, string_type,     state)
    class_actioncode = bootstrap_type("ActionCode", scd_root, actioncode_type, state)
    class_bytes      = bootstrap_type("Bytes",      scd_root, bytes_type,      state)

    # Can only create constraints after ActionCode type has been created:
    bootstrap_constraint(class_integer,    "Integer",    "int",   scd_root, integer_type,    actioncode_type, state)
    bootstrap_constraint(class_type,       "Type",       "tuple", scd_root, type_type,       actioncode_type, state)
    bootstrap_constraint(class_boolean,    "Boolean",    "bool",  scd_root, boolean_type,    actioncode_type, state)
    bootstrap_constraint(class_float,      "Float",      "float", scd_root, float_type,      actioncode_type, state)
    bootstrap_constraint(class_string,     "String",     "str",   scd_root, string_type,     actioncode_type, state)
    bootstrap_constraint(class_actioncode, "ActionCode", "str",   scd_root, actioncode_type, actioncode_type, state)
    bootstrap_constraint(class_bytes,      "Bytes",      "bytes", scd_root, bytes_type,      actioncode_type, state)
