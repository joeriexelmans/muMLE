from state.base import State, UUID
from services.bottom.V0 import Bottom


def create_model_root(bottom: Bottom, model_name: str) -> UUID:
    model_root = bottom.create_node()
    mcl_root_id = bottom.create_node(value=str(model_root))
    bottom.create_edge(bottom.model, mcl_root_id, label=model_name)
    return model_root


def bootstrap_scd(state: State) -> UUID:
    # init model roots and store their UUIDs attached to state root
    state_root = state.read_root()
    bottom = Bottom(state_root, state)
    mcl_root = create_model_root(bottom, "SCD")
    mcl_morphism_root = create_model_root(bottom, "phi(SCD,SCD)")

    # Create model roots for primitive types
    integer_type_root = create_model_root(bottom, "Integer")
    boolean_type_root = create_model_root(bottom, "Boolean")
    string_type_root = create_model_root(bottom, "String")
    float_type_root = create_model_root(bottom, "Float")
    type_type_root = create_model_root(bottom, "Type")

    # create MCL, without morphism links
    bottom = Bottom(mcl_root, state)

    def add_node_element(element_name, node_value=None):
        """ Helper function, adds node to model with given name and value """
        _node = bottom.create_node(value=node_value)
        bottom.create_edge(bottom.model, _node, element_name)
        return _node

    def add_edge_element(element_name, source, target):
        """ Helper function, adds edge to model with given name """
        _edge = bottom.create_edge(source, target)
        bottom.create_edge(bottom.model, _edge, element_name)
        return _edge

    def add_attribute_attributes(attribute_element_name, attribute_element, _name, _optional):
        _name_node = add_node_element(f"{attribute_element_name}.name", _name)
        _name_edge = add_edge_element(f"{attribute_element_name}01", attribute_element, _name_node)
        _optional_node = add_node_element(f"{attribute_element_name}.optional", _optional)
        _optional_edge = add_edge_element(f"{attribute_element_name}02", attribute_element, _optional_node)
        return _name_node, _name_edge, _optional_node, _optional_edge

    # # CLASSES, i.e. elements typed by Class
    # # Element
    element_node = add_node_element("Element")
    # # Class
    class_node = add_node_element("Class")
    # # Attribute
    attr_node = add_node_element("Attribute")
    # # ModelRef
    model_ref_node = add_node_element("ModelRef")
    # # Global Constraint
    glob_constr_node = add_node_element("GlobalConstraint")
    # # ASSOCIATIONS, i.e. elements typed by Association
    # # Association
    assoc_edge = add_edge_element("Association", class_node, class_node)
    # # Inheritance
    inh_edge = add_edge_element("Inheritance", element_node, element_node)
    # # Attribute Link
    attr_link_edge = add_edge_element("AttributeLink", element_node, attr_node)
    # # INHERITANCES, i.e. elements typed by Inheritance
    # # Class inherits from Element
    class_inh_element_edge = add_edge_element("class_inh_element", class_node, element_node)
    # # Attribute inherits from Element
    attr_inh_element_edge = add_edge_element("attr_inh_element", attr_node, element_node)
    # # Association inherits from Element
    assoc_inh_element_edge = add_edge_element("assoc_inh_element", assoc_edge, element_node)
    # # AttributeLink inherits from Element
    attr_link_inh_element_edge = add_edge_element("attr_link_inh_element", attr_link_edge, element_node)
    # # ModelRef inherits from Attribute
    model_ref_inh_attr_edge = add_edge_element("model_ref_inh_attr", model_ref_node, attr_node)
    # # ATTRIBUTES, i.e. elements typed by Attribute
    # # Action Code # TODO: Update to ModelRef when action code is explicitly modelled
    action_code_node = add_node_element("ActionCode")
    # # MODELREFS, i.e. elements typed by ModelRef
    # # Integer
    integer_node = add_node_element("Integer", str(integer_type_root))
    # # String
    string_node = add_node_element("String", str(string_type_root))
    # # Boolean
    boolean_node = add_node_element("Boolean", str(boolean_type_root))
    # # ATTRIBUTE LINKS, i.e. elements typed by AttributeLink
    # # name attribute of AttributeLink
    attr_name_edge = add_edge_element("AttributeLink_name", attr_link_edge, string_node)
    # # optional attribute of AttributeLink
    attr_opt_edge = add_edge_element("AttributeLink_optional", attr_link_edge, boolean_node)
    # # constraint attribute of Element
    elem_constr_edge = add_edge_element("Element_constraint", element_node, action_code_node)
    # # abstract attribute of Class
    class_abs_edge = add_edge_element("Class_abstract", class_node, boolean_node)
    # # multiplicity attributes of Class
    class_l_c_edge = add_edge_element("Class_lower_cardinality", class_node, integer_node)
    class_u_c_edge = add_edge_element("Class_upper_cardinality", class_node, integer_node)
    # # multiplicity attributes of Association
    assoc_s_l_c_edge = add_edge_element("Association_source_lower_cardinality", assoc_edge, integer_node)
    assoc_s_u_c_edge = add_edge_element("Association_source_upper_cardinality", assoc_edge, integer_node)
    assoc_t_l_c_edge = add_edge_element("Association_target_lower_cardinality", assoc_edge, integer_node)
    assoc_t_u_c_edge = add_edge_element("Association_target_upper_cardinality", assoc_edge, integer_node)
    # # ATTRIBUTE ATTRIBUTES, assign 'name' and 'optional' attributes to all AttributeLinks
    # # AttributeLink_name
    attr_name_name_node, attr_name_name_edge, attr_name_optional_node, attr_name_optional_edge = \
        add_attribute_attributes("AttributeLink_name", attr_name_edge, "name", False)
    # # AttributeLink_opt
    attr_opt_name_node, attr_opt_name_edge, attr_opt_optional_node, attr_opt_optional_edge = \
        add_attribute_attributes("AttributeLink_optional", attr_opt_edge, "optional", False)
    # # Element_constraint
    elem_constr_name_node, elem_constr_name_edge, elem_constr_optional_node, elem_constr_optional_edge = \
        add_attribute_attributes("Element_constraint", elem_constr_edge, "constraint", True)
    # # Class_abstract
    class_abs_name_node, class_abs_name_edge, class_abs_optional_node, class_abs_optional_edge = \
        add_attribute_attributes("Class_abstract", class_abs_edge, "abstract", True)
    # # Class_lower_cardinality
    class_l_c_name_node, class_l_c_name_edge, class_l_c_optional_node, class_l_c_optional_edge = \
        add_attribute_attributes("Class_lower_cardinality", class_l_c_edge, "lower_cardinality", True)
    # # Class_upper_cardinality
    class_u_c_name_node, class_u_c_name_edge, class_u_c_optional_node, class_u_c_optional_edge = \
        add_attribute_attributes("Class_upper_cardinality", class_u_c_edge, "upper_cardinality", True)
    # # Association_source_lower_cardinality
    assoc_s_l_c_name_node, assoc_s_l_c_name_edge, assoc_s_l_c_optional_node, assoc_s_l_c_optional_edge = \
        add_attribute_attributes("Association_source_lower_cardinality", assoc_s_l_c_edge, "source_lower_cardinality", True)
    # # Association_source_upper_cardinality
    assoc_s_u_c_name_node, assoc_s_u_c_name_edge, assoc_s_u_c_optional_node, assoc_s_u_c_optional_edge = \
        add_attribute_attributes("Association_source_upper_cardinality", assoc_s_u_c_edge, "source_upper_cardinality", True)
    # # Association_target_lower_cardinality
    assoc_t_l_c_name_node, assoc_t_l_c_name_edge, assoc_t_l_c_optional_node, assoc_t_l_c_optional_edge = \
        add_attribute_attributes("Association_target_lower_cardinality", assoc_t_l_c_edge, "target_lower_cardinality", True)
    # # Association_target_upper_cardinality
    assoc_t_u_c_name_node, assoc_t_u_c_name_edge, assoc_t_u_c_optional_node, assoc_t_u_c_optional_edge = \
        add_attribute_attributes("Association_target_upper_cardinality", assoc_t_u_c_edge, "target_upper_cardinality", True)

    # create phi(SCD,SCD) to type MCL with itself


def bootstrap_type_type(model_root: UUID, state: State) -> UUID:
    pass


def bootstrap_boolean_type(model_root: UUID, state: State) -> UUID:
    pass


def bootstrap_integer_type(model_root: UUID, state: State) -> UUID:
    pass


def bootstrap_float_type(model_root: UUID, state: State) -> UUID:
    pass


def bootstrap_string_type(model_root: UUID, state: State) -> UUID:
    pass
