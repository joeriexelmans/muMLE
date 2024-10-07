from state.base import State, UUID
from services.bottom.V0 import Bottom
from services.primitives.boolean_type import Boolean
from services.primitives.string_type import String
from bootstrap.primitive import (
    bootstrap_primitive_types
    # bootstrap_boolean_type,
    # bootstrap_float_type,
    # bootstrap_integer_type,
    # bootstrap_string_type,
    # bootstrap_type_type,
    # bootstrap_actioncode_type
)


def create_model_root(bottom: Bottom, model_name: str) -> UUID:
    model_root = bottom.create_node()
    mcl_root_id = bottom.create_node(value=str(model_root))
    bottom.create_edge(bottom.state.read_root(), mcl_root_id, label=model_name)
    return model_root


def bootstrap_scd(state: State) -> UUID:
    # init model roots and store their UUIDs attached to state root
    bottom = Bottom(state)
    mcl_root = create_model_root(bottom, "SCD")

    # Create model roots for primitive types
    integer_type_root = create_model_root(bottom, "Integer")
    boolean_type_root = create_model_root(bottom, "Boolean")
    string_type_root = create_model_root(bottom, "String")
    float_type_root = create_model_root(bottom, "Float")
    type_type_root = create_model_root(bottom, "Type")
    actioncode_type_root = create_model_root(bottom, "ActionCode")

    # create MCL, without morphism links

    def add_node_element(element_name, node_value=None):
        """ Helper function, adds node to model with given name and value """
        _node = bottom.create_node(value=node_value)
        bottom.create_edge(mcl_root, _node, element_name)
        return _node

    def add_edge_element(element_name, source, target):
        """ Helper function, adds edge to model with given name """
        _edge = bottom.create_edge(source, target)
        bottom.create_edge(mcl_root, _edge, element_name)
        return _edge

    def add_attribute_attributes(attribute_element_name, attribute_element):
        _name_model = bottom.create_node()
        _name_node = add_node_element(f"{attribute_element_name}.name", str(_name_model))
        _name_edge = add_edge_element(f"{attribute_element_name}_name", attribute_element, _name_node)
        _optional_model = bottom.create_node()
        _optional_node = add_node_element(f"{attribute_element_name}.optional", str(_optional_model))
        _optional_edge = add_edge_element(f"{attribute_element_name}_optional", attribute_element, _optional_node)
        return _name_model, _optional_model

    ##### SCD META-MODEL #####

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
    add_edge_element("class_inh_element", class_node, element_node)
    # # GlobalConstraint inherits from Element
    add_edge_element("gc_inh_element", glob_constr_node, element_node)
    # # Attribute inherits from Element
    add_edge_element("attr_inh_element", attr_node, element_node)
    # # Association inherits from Element
    add_edge_element("assoc_inh_element", assoc_edge, element_node)
    # # AttributeLink inherits from Element
    add_edge_element("attr_link_inh_element", attr_link_edge, element_node)
    # # ModelRef inherits from Attribute
    add_edge_element("model_ref_inh_attr", model_ref_node, attr_node)

    # # ATTRIBUTES, i.e. elements typed by Attribute
    # # Action Code # TODO: Update to ModelRef when action code is explicitly modelled
    # action_code_node = add_node_element("ActionCode")

    # # MODELREFS, i.e. elements typed by ModelRef
    # # Integer
    integer_node = add_node_element("Integer", str(integer_type_root))
    # # String
    string_node = add_node_element("String", str(string_type_root))
    # # Boolean
    boolean_node = add_node_element("Boolean", str(boolean_type_root))
    # # ActionCode
    actioncode_node = add_node_element("ActionCode", str(actioncode_type_root))

    # # ATTRIBUTE LINKS, i.e. elements typed by AttributeLink
    # # name attribute of AttributeLink
    attr_name_edge = add_edge_element("AttributeLink_name", attr_link_edge, string_node)
    # # optional attribute of AttributeLink
    attr_opt_edge = add_edge_element("AttributeLink_optional", attr_link_edge, boolean_node)
    # # constraint attribute of Element
    elem_constr_edge = add_edge_element("Element_constraint", element_node, actioncode_node)
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

    # # bootstrap primitive types
    bootstrap_primitive_types(mcl_root, state,
        integer_type_root,
        boolean_type_root,
        float_type_root,
        string_type_root,
        type_type_root,
        actioncode_type_root)
    # bootstrap_integer_type(mcl_root, integer_type_root, integer_type_root, actioncode_type_root, state)
    # bootstrap_boolean_type(mcl_root, boolean_type_root, integer_type_root, actioncode_type_root, state)
    # bootstrap_float_type(mcl_root, float_type_root, integer_type_root, actioncode_type_root, state)
    # bootstrap_string_type(mcl_root, string_type_root, integer_type_root, actioncode_type_root, state)
    # bootstrap_type_type(mcl_root, type_type_root, integer_type_root, actioncode_type_root, state)
    # bootstrap_actioncode_type(mcl_root, actioncode_type_root, integer_type_root, actioncode_type_root, state)

    # # ATTRIBUTE ATTRIBUTES, assign 'name' and 'optional' attributes to all AttributeLinks
    # # AttributeLink_name
    m_name, m_opt = add_attribute_attributes("AttributeLink_name", attr_name_edge)
    String(m_name, state).create("name")
    Boolean(m_opt, state).create(False)
    # # AttributeLink_opt
    m_name, m_opt = add_attribute_attributes("AttributeLink_optional", attr_opt_edge)
    String(m_name, state).create("optional")
    Boolean(m_opt, state).create(False)
    # # Element_constraint
    m_name, m_opt = add_attribute_attributes("Element_constraint", elem_constr_edge)
    String(m_name, state).create("constraint")
    Boolean(m_opt, state).create(True)
    # # Class_abstract
    m_name, m_opt = add_attribute_attributes("Class_abstract", class_abs_edge)
    String(m_name, state).create("abstract")
    Boolean(m_opt, state).create(True)
    # # Class_lower_cardinality
    m_name, m_opt = add_attribute_attributes("Class_lower_cardinality", class_l_c_edge)
    String(m_name, state).create("lower_cardinality")
    Boolean(m_opt, state).create(True)
    # # Class_upper_cardinality
    m_name, m_opt = add_attribute_attributes("Class_upper_cardinality", class_u_c_edge)
    String(m_name, state).create("upper_cardinality")
    Boolean(m_opt, state).create(True)
    # # Association_source_lower_cardinality
    m_name, m_opt = add_attribute_attributes("Association_source_lower_cardinality", assoc_s_l_c_edge)
    String(m_name, state).create("source_lower_cardinality")
    Boolean(m_opt, state).create(True)
    # # Association_source_upper_cardinality
    m_name, m_opt = add_attribute_attributes("Association_source_upper_cardinality", assoc_s_u_c_edge)
    String(m_name, state).create("source_upper_cardinality")
    Boolean(m_opt, state).create(True)
    # # Association_target_lower_cardinality
    m_name, m_opt = add_attribute_attributes("Association_target_lower_cardinality", assoc_t_l_c_edge)
    String(m_name, state).create("target_lower_cardinality")
    Boolean(m_opt, state).create(True)
    # # Association_target_upper_cardinality
    m_name, m_opt = add_attribute_attributes("Association_target_upper_cardinality", assoc_t_u_c_edge)
    String(m_name, state).create("target_upper_cardinality")
    Boolean(m_opt, state).create(True)
    # # Make Element abstract
    abs_model = bottom.create_node()
    abs_node = add_node_element(f"Element.abstract", str(abs_model))
    abs_edge = add_edge_element(f"Element_abstract", element_node, abs_node)
    Boolean(abs_model, state).create(True)

    # create phi(SCD,SCD) to type MCL with itself

    def add_mcl_morphism(element_name, type_name):
        # get elements from mcl by name
        _element_edge, = bottom.read_outgoing_edges(mcl_root, element_name)
        _element_node = bottom.read_edge_target(_element_edge)
        _type_edge, = bottom.read_outgoing_edges(mcl_root, type_name)
        _type_node = bottom.read_edge_target(_type_edge)
        # create morphism link
        bottom.create_edge(_element_node, _type_node, "Morphism")

    # Class
    add_mcl_morphism("Element", "Class")
    add_mcl_morphism("Class", "Class")
    add_mcl_morphism("Attribute", "Class")
    add_mcl_morphism("ModelRef", "Class")
    add_mcl_morphism("GlobalConstraint", "Class")
    # Association
    add_mcl_morphism("Association", "Association")
    add_mcl_morphism("Inheritance", "Association")
    add_mcl_morphism("AttributeLink", "Association")
    # Inheritance
    add_mcl_morphism("class_inh_element", "Inheritance")
    add_mcl_morphism("gc_inh_element", "Inheritance")
    add_mcl_morphism("attr_inh_element", "Inheritance")
    add_mcl_morphism("assoc_inh_element", "Inheritance")
    add_mcl_morphism("attr_link_inh_element", "Inheritance")
    add_mcl_morphism("model_ref_inh_attr", "Inheritance")
    # Attribute
    # add_mcl_morphism("ActionCode", "Attribute")
    # ModelRef
    add_mcl_morphism("Integer", "ModelRef")
    add_mcl_morphism("String", "ModelRef")
    add_mcl_morphism("Boolean", "ModelRef")
    add_mcl_morphism("ActionCode", "ModelRef")
    # AttributeLink
    add_mcl_morphism("AttributeLink_name", "AttributeLink")
    add_mcl_morphism("AttributeLink_optional", "AttributeLink")
    add_mcl_morphism("Element_constraint", "AttributeLink")
    add_mcl_morphism("Class_abstract", "AttributeLink")
    add_mcl_morphism("Class_lower_cardinality", "AttributeLink")
    add_mcl_morphism("Class_upper_cardinality", "AttributeLink")
    add_mcl_morphism("Association_source_lower_cardinality", "AttributeLink")
    add_mcl_morphism("Association_source_upper_cardinality", "AttributeLink")
    add_mcl_morphism("Association_target_lower_cardinality", "AttributeLink")
    add_mcl_morphism("Association_target_upper_cardinality", "AttributeLink")
    # AttributeLink_name
    add_mcl_morphism("AttributeLink_name_name", "AttributeLink_name")
    add_mcl_morphism("AttributeLink_optional_name", "AttributeLink_name")
    add_mcl_morphism("Element_constraint_name", "AttributeLink_name")
    add_mcl_morphism("Class_abstract_name", "AttributeLink_name")
    add_mcl_morphism("Class_lower_cardinality_name", "AttributeLink_name")
    add_mcl_morphism("Class_upper_cardinality_name", "AttributeLink_name")
    add_mcl_morphism("Association_source_lower_cardinality_name", "AttributeLink_name")
    add_mcl_morphism("Association_source_upper_cardinality_name", "AttributeLink_name")
    add_mcl_morphism("Association_target_lower_cardinality_name", "AttributeLink_name")
    add_mcl_morphism("Association_target_upper_cardinality_name", "AttributeLink_name")
    # AttributeLink_optional
    add_mcl_morphism("AttributeLink_name_optional", "AttributeLink_optional")
    add_mcl_morphism("AttributeLink_optional_optional", "AttributeLink_optional")
    add_mcl_morphism("Element_constraint_optional", "AttributeLink_optional")
    add_mcl_morphism("Class_abstract_optional", "AttributeLink_optional")
    add_mcl_morphism("Class_lower_cardinality_optional", "AttributeLink_optional")
    add_mcl_morphism("Class_upper_cardinality_optional", "AttributeLink_optional")
    add_mcl_morphism("Association_source_lower_cardinality_optional", "AttributeLink_optional")
    add_mcl_morphism("Association_source_upper_cardinality_optional", "AttributeLink_optional")
    add_mcl_morphism("Association_target_lower_cardinality_optional", "AttributeLink_optional")
    add_mcl_morphism("Association_target_upper_cardinality_optional", "AttributeLink_optional")
    # String
    add_mcl_morphism("AttributeLink_name.name", "String")
    add_mcl_morphism("AttributeLink_optional.name", "String")
    add_mcl_morphism("Element_constraint.name", "String")
    add_mcl_morphism("Class_abstract.name", "String")
    add_mcl_morphism("Class_lower_cardinality.name", "String")
    add_mcl_morphism("Class_upper_cardinality.name", "String")
    add_mcl_morphism("Association_source_lower_cardinality.name", "String")
    add_mcl_morphism("Association_source_upper_cardinality.name", "String")
    add_mcl_morphism("Association_target_lower_cardinality.name", "String")
    add_mcl_morphism("Association_target_upper_cardinality.name", "String")
    # Boolean
    add_mcl_morphism("AttributeLink_name.optional", "Boolean")
    add_mcl_morphism("AttributeLink_optional.optional", "Boolean")
    add_mcl_morphism("Element_constraint.optional", "Boolean")
    add_mcl_morphism("Class_abstract.optional", "Boolean")
    add_mcl_morphism("Class_lower_cardinality.optional", "Boolean")
    add_mcl_morphism("Class_upper_cardinality.optional", "Boolean")
    add_mcl_morphism("Association_source_lower_cardinality.optional", "Boolean")
    add_mcl_morphism("Association_source_upper_cardinality.optional", "Boolean")
    add_mcl_morphism("Association_target_lower_cardinality.optional", "Boolean")
    add_mcl_morphism("Association_target_upper_cardinality.optional", "Boolean")
    add_mcl_morphism("Element.abstract", "Boolean")
    # Class_abstract
    add_mcl_morphism("Element_abstract", "Class_abstract")

    return mcl_root


if __name__ == '__main__':
    from state.devstate import DevState as State
    s = State()
    bootstrap_scd(s)
    r = s.read_root()
    for n in s.read_dict_keys(r):
        print(s.read_value(n))
