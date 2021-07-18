from core.element import Element
from state.base import State, STRING, INTEGER, BOOLEAN, TYPE
from core.context.generic import GenericContext


class SCDContext(GenericContext):
    def __init__(self, state: State, model: Element, metamodel: Element):
        super().__init__(state, model, metamodel)

    def _bootstrap_scd(self) -> Element:

        scd = self.state.create_nodevalue("SimpleClassDiagrams")
        self.state.create_dict(self.state.read_root(), "SimpleClassDiagrams", scd)
        self.state.create_dict(scd, "Model", self.state.create_node())
        self.state.create_dict(scd, "Metamodel", scd)
        super().__init__(self.state, Element(id=scd), Element(id=scd))

        # Classes --> elements that will be typed by Class
        self.bottom.add_node(Element(value="Element"))
        self.bottom.add_node(Element(value="Class"))
        self.bottom.add_value(Element(value="Attribute"), Element(value=TYPE))

        # Associations --> elements that will be typed by Association
        self.bottom.add_edge(Element(value="Association"), Element(value="Class"), Element(value="Class"))
        self.bottom.add_edge(Element(value="Inheritance"), Element(value="Element"), Element(value="Element"))
        self.bottom.add_edge(Element(value="AttributeLink"), Element(value="Element"), Element(value="Attribute"))

        # Attributes --> elements that will be typed by Attribute
        self.bottom.add_value(Element(value="Class_lower_cardinality"), Element(value=INTEGER))
        self.bottom.add_value(Element(value="Class_upper_cardinality"), Element(value=INTEGER))

        self.bottom.add_value(Element(value="Association_source_lower_cardinality"), Element(value=INTEGER))
        self.bottom.add_value(Element(value="Association_source_upper_cardinality"), Element(value=INTEGER))
        self.bottom.add_value(Element(value="Association_target_lower_cardinality"), Element(value=INTEGER))
        self.bottom.add_value(Element(value="Association_target_upper_cardinality"), Element(value=INTEGER))

        self.bottom.add_value(Element(value="Attribute_name"), Element(value=STRING))
        self.bottom.add_value(Element(value="Attribute_optional"), Element(value=BOOLEAN))

        # Attribute instances --> elements that will be typed by one of the Attributes defined above
        self.bottom.add_value(Element(value="Attribute_name.name"), Element(value="name"))
        self.bottom.add_value(Element(value="Attribute_name.optional"), Element(value=False))
        self.bottom.add_value(Element(value="Attribute_optional.name"), Element(value="optional"))
        self.bottom.add_value(Element(value="Attribute_optional.optional"), Element(value=False))

        self.bottom.add_value(Element(value="Class_lower_cardinality.name"), Element(value="lower_cardinality"))
        self.bottom.add_value(Element(value="Class_lower_cardinality.optional"), Element(value=True))
        self.bottom.add_value(Element(value="Class_upper_cardinality.name"), Element(value="upper_cardinality"))
        self.bottom.add_value(Element(value="Class_upper_cardinality.optional"), Element(value=True))

        self.bottom.add_value(Element(value="Association_source_lower_cardinality.name"), Element(value="source_lower_cardinality"))
        self.bottom.add_value(Element(value="Association_source_lower_cardinality.optional"), Element(value=True))
        self.bottom.add_value(Element(value="Association_source_upper_cardinality.name"), Element(value="source_upper_cardinality"))
        self.bottom.add_value(Element(value="Association_source_upper_cardinality.optional"), Element(value=True))

        self.bottom.add_value(Element(value="Association_target_lower_cardinality.name"), Element(value="target_lower_cardinality"))
        self.bottom.add_value(Element(value="Association_target_lower_cardinality.optional"), Element(value=True))
        self.bottom.add_value(Element(value="Association_target_upper_cardinality.name"), Element(value="target_upper_cardinality"))
        self.bottom.add_value(Element(value="Association_target_upper_cardinality.optional"), Element(value=True))

        # Inheritance instances --> elements that will be typed by Inheritance
        self.bottom.add_edge(Element(value="class_inh_element"), Element(value="Class"), Element(value="Element"))
        self.bottom.add_edge(Element(value="attribute_inh_element"), Element(value="Attribute"), Element(value="Element"))
        self.bottom.add_edge(Element(value="association_inh_element"), Element(value="Association"), Element(value="Element"))
        self.bottom.add_edge(Element(value="attributelink_inh_element"), Element(value="AttributeLink"), Element(value="Element"))

        # AttributeLinks --> elements that will be typed by AttributeLink
        self.bottom.add_edge(Element(value="Class_attr01"), Element(value="Class"), Element(value="Class_lower_cardinality"))
        self.bottom.add_edge(Element(value="Class_attr02"), Element(value="Class"), Element(value="Class_upper_cardinality"))

        self.bottom.add_edge(Element(value="Association_attr01"), Element(value="Association"), Element(value="Association_source_lower_cardinality"))
        self.bottom.add_edge(Element(value="Association_attr02"), Element(value="Association"), Element(value="Association_source_upper_cardinality"))
        self.bottom.add_edge(Element(value="Association_attr03"), Element(value="Association"), Element(value="Association_target_lower_cardinality"))
        self.bottom.add_edge(Element(value="Association_attr04"), Element(value="Association"), Element(value="Association_target_upper_cardinality"))

        self.bottom.add_edge(Element(value="Attribute_name_link"), Element(value="Attribute"), Element(value="Attribute_name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link"), Element(value="Attribute"), Element(value="Attribute_optional"))

        # AttributeLink instances --> elements that will be typed by one of the AttributeLink defined above
        self.bottom.add_edge(Element(value="Attribute_name_link_01"), Element(value="Attribute_name"), Element(value="Attribute_name.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_01"), Element(value="Attribute_name"), Element(value="Attribute_name.optional"))
        self.bottom.add_edge(Element(value="Attribute_name_link_02"), Element(value="Attribute_optional"), Element(value="Attribute_optional.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_02"), Element(value="Attribute_optional"), Element(value="Attribute_optional.optional"))

        self.bottom.add_edge(Element(value="Attribute_name_link_03"), Element(value="Class_lower_cardinality"), Element(value="Class_lower_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_03"), Element(value="Class_lower_cardinality"), Element(value="Class_lower_cardinality.optional"))
        self.bottom.add_edge(Element(value="Attribute_name_link_04"), Element(value="Class_upper_cardinality"), Element(value="Class_upper_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_04"), Element(value="Class_upper_cardinality"), Element(value="Class_upper_cardinality.optional"))

        self.bottom.add_edge(Element(value="Attribute_name_link_05"), Element(value="Association_source_lower_cardinality"), Element(value="Association_source_lower_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_05"), Element(value="Association_source_lower_cardinality"), Element(value="Association_source_lower_cardinality.optional"))
        self.bottom.add_edge(Element(value="Attribute_name_link_06"), Element(value="Association_source_upper_cardinality"), Element(value="Association_source_upper_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_06"), Element(value="Association_source_upper_cardinality"), Element(value="Association_source_upper_cardinality.optional"))

        self.bottom.add_edge(Element(value="Attribute_name_link_07"), Element(value="Association_target_lower_cardinality"), Element(value="Association_target_lower_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_07"), Element(value="Association_target_lower_cardinality"), Element(value="Association_target_lower_cardinality.optional"))
        self.bottom.add_edge(Element(value="Attribute_name_link_08"), Element(value="Association_target_upper_cardinality"), Element(value="Association_target_upper_cardinality.name"))
        self.bottom.add_edge(Element(value="Attribute_optional_link_08"), Element(value="Association_target_upper_cardinality"), Element(value="Association_target_upper_cardinality.optional"))

        """
        Retype the elements of the model.
        This way we make the model "metacircular".
        """
        self.retype_element(Element(value="Element"), Element(value="Class"))
        self.retype_element(Element(value="Class"), Element(value="Class"))
        self.retype_element(Element(value="Attribute"), Element(value="Class"))

        self.retype_element(Element(value="Association"), Element(value="Association"))
        self.retype_element(Element(value="Inheritance"), Element(value="Association"))
        self.retype_element(Element(value="AttributeLink"), Element(value="Association"))

        self.retype_element(Element(value="Class_lower_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Class_upper_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Association_source_lower_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Association_source_upper_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Association_target_lower_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Association_target_upper_cardinality"), Element(value="Attribute"))
        self.retype_element(Element(value="Attribute_name"), Element(value="Attribute"))
        self.retype_element(Element(value="Attribute_optional"), Element(value="Attribute"))

        self.retype_element(Element(value="Class_attr01"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Class_attr02"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Association_attr01"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Association_attr02"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Association_attr03"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Association_attr04"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Attribute_name_link"), Element(value="AttributeLink"))
        self.retype_element(Element(value="Attribute_optional_link"), Element(value="AttributeLink"))

        self.retype_element(Element(value="class_inh_element"), Element(value="Inheritance"))
        self.retype_element(Element(value="attribute_inh_element"), Element(value="Inheritance"))
        self.retype_element(Element(value="association_inh_element"), Element(value="Inheritance"))
        self.retype_element(Element(value="attributelink_inh_element"), Element(value="Inheritance"))

        self.retype_element(Element(value="Attribute_name.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Attribute_name.optional"),Element(value="Attribute_optional"))
        self.retype_element(Element(value="Attribute_optional.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Attribute_optional.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Class_lower_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Class_lower_cardinality.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Class_upper_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Class_upper_cardinality.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Association_source_lower_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Association_source_lower_cardinality.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Association_source_upper_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Association_source_upper_cardinality.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Association_target_lower_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Association_target_lower_cardinality.optional"), Element(value="Attribute_optional"))
        self.retype_element(Element(value="Association_target_upper_cardinality.name"), Element(value="Attribute_name"))
        self.retype_element(Element(value="Association_target_upper_cardinality.optional"), Element(value="Attribute_optional"))

        self.retype_element(Element(value="Attribute_name_link_01"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_01"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_02"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_02"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_03"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_03"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_04"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_04"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_05"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_05"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_06"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_06"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_07"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_07"), Element(value="Attribute_optional_link"))
        self.retype_element(Element(value="Attribute_name_link_08"), Element(value="Attribute_name_link"))
        self.retype_element(Element(value="Attribute_optional_link_08"), Element(value="Attribute_optional_link"))

        return Element(id=scd)


def main():
    from state.devstate import DevState

    s = DevState()
    scd = SCDContext(s, Element(), Element())
    bootstrap = scd._bootstrap_scd()
    model = s.read_dict(bootstrap.id, "Model")
    x = []
    for e in s.read_outgoing(model):
        label_node_edge, = s.read_outgoing(e)
        _, label_node = s.read_edge(label_node_edge)
        type_node = s.read_dict(label_node, "Type")
        x.append(f"{s.read_value(label_node)} : {s.read_value(type_node)}")
    for t in sorted(x):
        print(t)

    # s.dump("out/scd.dot", "out/scd.png")


if __name__ == '__main__':
    main()
