from state.base import State, UUID
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer


def bootstrap_type(type_name: str, python_type: str, scd_root: UUID, model_root: UUID, state: State):
    bottom = Bottom(state)
    # create class
    class_node = bottom.create_node()  # create class node
    bottom.create_edge(model_root, class_node, type_name)  # attach to model
    scd_node, = bottom.read_outgoing_elements(scd_root, "Class")  # retrieve type
    bottom.create_edge(class_node, scd_node, "Morphism")  # create morphism link
    # set min_cardinality
    min_c_model = bottom.create_node()
    Integer(min_c_model, state).create(1)
    min_c_node = bottom.create_node(str(min_c_model))
    bottom.create_edge(model_root, min_c_node, f"{type_name}.lower_cardinality")
    min_c_link = bottom.create_edge(class_node, min_c_node)
    bottom.create_edge(model_root, min_c_link, f"{type_name}.lower_cardinality_link")
    scd_node, = bottom.read_outgoing_elements(scd_root, "Integer")
    scd_link, = bottom.read_outgoing_elements(scd_root, "Class_lower_cardinality")
    bottom.create_edge(min_c_node, scd_node, "Morphism")
    bottom.create_edge(min_c_link, scd_link, "Morphism")
    # set max_cardinality
    max_c_model = bottom.create_node()
    Integer(max_c_model, state).create(1)
    max_c_node = bottom.create_node(str(max_c_model))
    bottom.create_edge(model_root, max_c_node, f"{type_name}.upper_cardinality")
    max_c_link = bottom.create_edge(class_node, max_c_node)
    bottom.create_edge(model_root, max_c_link, f"{type_name}.upper_cardinality_link")
    scd_node, = bottom.read_outgoing_elements(scd_root, "Integer")
    scd_link, = bottom.read_outgoing_elements(scd_root, "Class_upper_cardinality")
    bottom.create_edge(max_c_node, scd_node, "Morphism")
    bottom.create_edge(max_c_link, scd_link, "Morphism")
    # set constraint
    constraint_node = bottom.create_node(f"isinstance(read_value(element),{python_type})")
    bottom.create_edge(model_root, constraint_node, f"{type_name}.constraint")
    constraint_link = bottom.create_edge(class_node, constraint_node)
    bottom.create_edge(model_root, constraint_link, f"{type_name}.constraint_link")
    scd_node, = bottom.read_outgoing_elements(scd_root, "ActionCode")
    scd_link, = bottom.read_outgoing_elements(scd_root, "Element_constraint")
    bottom.create_edge(constraint_node, scd_node, "Morphism")
    bottom.create_edge(constraint_link, scd_link, "Morphism")
    

def bootstrap_type_type(scd_root: UUID, model_root: UUID, state: State):
    bootstrap_type("Type", "tuple", scd_root, model_root, state)


def bootstrap_boolean_type(scd_root: UUID, model_root: UUID, state: State):
    bootstrap_type("Boolean", "bool", scd_root, model_root, state)


def bootstrap_integer_type(scd_root: UUID, model_root: UUID, state: State):
    bootstrap_type("Integer", "int", scd_root, model_root, state)


def bootstrap_float_type(scd_root: UUID, model_root: UUID, state: State):
    bootstrap_type("Float", "float", scd_root, model_root, state)


def bootstrap_string_type(scd_root: UUID, model_root: UUID, state: State):
    bootstrap_type("String", "str", scd_root, model_root, state)
