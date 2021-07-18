from core.element import Element
from state.base import State, STRING, INTEGER, BOOLEAN, TYPE
from core.context.generic import GenericContext


def bootstrap_scd(state: State) -> Element:
    ctx = GenericContext(state, Element(), Element())

    scd = state.create_nodevalue("SimpleClassDiagrams")
    state.create_dict(state.read_root(), "SimpleClassDiagrams", scd)
    state.create_dict(scd, "Model", state.create_node())
    state.create_dict(scd, "Metamodel", scd)
    ctx.__init__(state, Element(id=scd), Element(id=scd))

    # Classes --> elements that will be typed by Class
    ctx.bottom.add_node(Element(value="Element"))
    ctx.bottom.add_node(Element(value="Class"))
    ctx.bottom.add_value(Element(value="Attribute"), Element(value=TYPE))

    # Associations --> elements that will be typed by Association
    ctx.bottom.add_edge(Element(value="Association"), Element(value="Class"), Element(value="Class"))
    ctx.bottom.add_edge(Element(value="Inheritance"), Element(value="Element"), Element(value="Element"))
    ctx.bottom.add_edge(Element(value="AttributeLink"), Element(value="Element"), Element(value="Attribute"))

    # Attributes --> elements that will be typed by Attribute
    ctx.bottom.add_value(Element(value="Class_lower_cardinality"), Element(value=INTEGER))
    ctx.bottom.add_value(Element(value="Class_upper_cardinality"), Element(value=INTEGER))

    ctx.bottom.add_value(Element(value="Association_source_lower_cardinality"), Element(value=INTEGER))
    ctx.bottom.add_value(Element(value="Association_source_upper_cardinality"), Element(value=INTEGER))
    ctx.bottom.add_value(Element(value="Association_target_lower_cardinality"), Element(value=INTEGER))
    ctx.bottom.add_value(Element(value="Association_target_upper_cardinality"), Element(value=INTEGER))

    ctx.bottom.add_value(Element(value="Attribute_name"), Element(value=STRING))
    ctx.bottom.add_value(Element(value="Attribute_optional"), Element(value=BOOLEAN))

    # Attribute instances --> elements that will be typed by one of the Attributes defined above
    ctx.bottom.add_value(Element(value="Attribute_name.name"), Element(value="name"))
    ctx.bottom.add_value(Element(value="Attribute_name.optional"), Element(value=False))
    ctx.bottom.add_value(Element(value="Attribute_optional.name"), Element(value="optional"))
    ctx.bottom.add_value(Element(value="Attribute_optional.optional"), Element(value=False))

    ctx.bottom.add_value(Element(value="Class_lower_cardinality.name"), Element(value="lower_cardinality"))
    ctx.bottom.add_value(Element(value="Class_lower_cardinality.optional"), Element(value=True))
    ctx.bottom.add_value(Element(value="Class_upper_cardinality.name"), Element(value="upper_cardinality"))
    ctx.bottom.add_value(Element(value="Class_upper_cardinality.optional"), Element(value=True))

    ctx.bottom.add_value(Element(value="Association_source_lower_cardinality.name"),
                         Element(value="source_lower_cardinality"))
    ctx.bottom.add_value(Element(value="Association_source_lower_cardinality.optional"), Element(value=True))
    ctx.bottom.add_value(Element(value="Association_source_upper_cardinality.name"),
                         Element(value="source_upper_cardinality"))
    ctx.bottom.add_value(Element(value="Association_source_upper_cardinality.optional"), Element(value=True))

    ctx.bottom.add_value(Element(value="Association_target_lower_cardinality.name"),
                         Element(value="target_lower_cardinality"))
    ctx.bottom.add_value(Element(value="Association_target_lower_cardinality.optional"), Element(value=True))
    ctx.bottom.add_value(Element(value="Association_target_upper_cardinality.name"),
                         Element(value="target_upper_cardinality"))
    ctx.bottom.add_value(Element(value="Association_target_upper_cardinality.optional"), Element(value=True))

    # Inheritance instances --> elements that will be typed by Inheritance
    ctx.bottom.add_edge(Element(value="class_inh_element"), Element(value="Class"), Element(value="Element"))
    ctx.bottom.add_edge(Element(value="attribute_inh_element"), Element(value="Attribute"), Element(value="Element"))
    ctx.bottom.add_edge(Element(value="association_inh_element"), Element(value="Association"),
                        Element(value="Element"))
    ctx.bottom.add_edge(Element(value="attributelink_inh_element"), Element(value="AttributeLink"),
                        Element(value="Element"))

    # AttributeLinks --> elements that will be typed by AttributeLink
    ctx.bottom.add_edge(Element(value="Class_attr01"), Element(value="Class"),
                        Element(value="Class_lower_cardinality"))
    ctx.bottom.add_edge(Element(value="Class_attr02"), Element(value="Class"),
                        Element(value="Class_upper_cardinality"))

    ctx.bottom.add_edge(Element(value="Association_attr01"), Element(value="Association"),
                        Element(value="Association_source_lower_cardinality"))
    ctx.bottom.add_edge(Element(value="Association_attr02"), Element(value="Association"),
                        Element(value="Association_source_upper_cardinality"))
    ctx.bottom.add_edge(Element(value="Association_attr03"), Element(value="Association"),
                        Element(value="Association_target_lower_cardinality"))
    ctx.bottom.add_edge(Element(value="Association_attr04"), Element(value="Association"),
                        Element(value="Association_target_upper_cardinality"))

    ctx.bottom.add_edge(Element(value="Attribute_name_link"), Element(value="Attribute"),
                        Element(value="Attribute_name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link"), Element(value="Attribute"),
                        Element(value="Attribute_optional"))

    # AttributeLink instances --> elements that will be typed by one of the AttributeLink defined above
    ctx.bottom.add_edge(Element(value="Attribute_name_link_01"), Element(value="Attribute_name"),
                        Element(value="Attribute_name.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_01"), Element(value="Attribute_name"),
                        Element(value="Attribute_name.optional"))
    ctx.bottom.add_edge(Element(value="Attribute_name_link_02"), Element(value="Attribute_optional"),
                        Element(value="Attribute_optional.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_02"), Element(value="Attribute_optional"),
                        Element(value="Attribute_optional.optional"))

    ctx.bottom.add_edge(Element(value="Attribute_name_link_03"), Element(value="Class_lower_cardinality"),
                        Element(value="Class_lower_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_03"), Element(value="Class_lower_cardinality"),
                        Element(value="Class_lower_cardinality.optional"))
    ctx.bottom.add_edge(Element(value="Attribute_name_link_04"), Element(value="Class_upper_cardinality"),
                        Element(value="Class_upper_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_04"), Element(value="Class_upper_cardinality"),
                        Element(value="Class_upper_cardinality.optional"))

    ctx.bottom.add_edge(Element(value="Attribute_name_link_05"), Element(value="Association_source_lower_cardinality"),
                        Element(value="Association_source_lower_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_05"),
                        Element(value="Association_source_lower_cardinality"),
                        Element(value="Association_source_lower_cardinality.optional"))
    ctx.bottom.add_edge(Element(value="Attribute_name_link_06"), Element(value="Association_source_upper_cardinality"),
                        Element(value="Association_source_upper_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_06"),
                        Element(value="Association_source_upper_cardinality"),
                        Element(value="Association_source_upper_cardinality.optional"))

    ctx.bottom.add_edge(Element(value="Attribute_name_link_07"), Element(value="Association_target_lower_cardinality"),
                        Element(value="Association_target_lower_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_07"),
                        Element(value="Association_target_lower_cardinality"),
                        Element(value="Association_target_lower_cardinality.optional"))
    ctx.bottom.add_edge(Element(value="Attribute_name_link_08"), Element(value="Association_target_upper_cardinality"),
                        Element(value="Association_target_upper_cardinality.name"))
    ctx.bottom.add_edge(Element(value="Attribute_optional_link_08"),
                        Element(value="Association_target_upper_cardinality"),
                        Element(value="Association_target_upper_cardinality.optional"))

    """
    Retype the elements of the model.
    This way we make the model "metacircular".
    """
    ctx.retype_element(Element(value="Element"), Element(value="Class"))
    ctx.retype_element(Element(value="Class"), Element(value="Class"))
    ctx.retype_element(Element(value="Attribute"), Element(value="Class"))

    ctx.retype_element(Element(value="Association"), Element(value="Association"))
    ctx.retype_element(Element(value="Inheritance"), Element(value="Association"))
    ctx.retype_element(Element(value="AttributeLink"), Element(value="Association"))

    ctx.retype_element(Element(value="Class_lower_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Class_upper_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Association_source_lower_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Association_source_upper_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Association_target_lower_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Association_target_upper_cardinality"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Attribute_name"), Element(value="Attribute"))
    ctx.retype_element(Element(value="Attribute_optional"), Element(value="Attribute"))

    ctx.retype_element(Element(value="Class_attr01"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Class_attr02"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Association_attr01"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Association_attr02"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Association_attr03"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Association_attr04"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Attribute_name_link"), Element(value="AttributeLink"))
    ctx.retype_element(Element(value="Attribute_optional_link"), Element(value="AttributeLink"))

    ctx.retype_element(Element(value="class_inh_element"), Element(value="Inheritance"))
    ctx.retype_element(Element(value="attribute_inh_element"), Element(value="Inheritance"))
    ctx.retype_element(Element(value="association_inh_element"), Element(value="Inheritance"))
    ctx.retype_element(Element(value="attributelink_inh_element"), Element(value="Inheritance"))

    ctx.retype_element(Element(value="Attribute_name.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Attribute_name.optional"), Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Attribute_optional.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Attribute_optional.optional"), Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Class_lower_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Class_lower_cardinality.optional"), Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Class_upper_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Class_upper_cardinality.optional"), Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Association_source_lower_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Association_source_lower_cardinality.optional"),
                       Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Association_source_upper_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Association_source_upper_cardinality.optional"),
                       Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Association_target_lower_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Association_target_lower_cardinality.optional"),
                       Element(value="Attribute_optional"))
    ctx.retype_element(Element(value="Association_target_upper_cardinality.name"), Element(value="Attribute_name"))
    ctx.retype_element(Element(value="Association_target_upper_cardinality.optional"),
                       Element(value="Attribute_optional"))

    ctx.retype_element(Element(value="Attribute_name_link_01"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_01"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_02"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_02"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_03"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_03"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_04"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_04"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_05"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_05"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_06"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_06"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_07"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_07"), Element(value="Attribute_optional_link"))
    ctx.retype_element(Element(value="Attribute_name_link_08"), Element(value="Attribute_name_link"))
    ctx.retype_element(Element(value="Attribute_optional_link_08"), Element(value="Attribute_optional_link"))

    return Element(id=scd)
