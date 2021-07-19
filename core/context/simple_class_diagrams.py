from core.element import Element, String, Integer, Boolean
from state.base import State
from core.context.generic import GenericContext


class SCDContext(GenericContext):
    def __init__(self, state: State, model: Element, metamodel: Element):
        super().__init__(state, model, metamodel)

    def exposed_methods(self):
        yield from super().exposed_methods()
        yield from [
            self.create_class,
            self.create_class_attribute,
            self.create_association,
            self.create_inheritance
        ]

    def create_class(self, name: String, lower_cardinality: Integer = Element(), upper_cardinality: Integer = Element()):
        self.instantiate(Element(value="Class"), name)
        if lower_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Class_lower_cardinality"),
                Element(value=name.value + ".lower_cardinality"),
                lower_cardinality
            )
            self.instantiate_link(
                Element(value="Class_lower_cardinality_link"),
                Element(value=name.value + ".lower_cardinality_link"),
                name,
                Element(value=name.value + ".lower_cardinality")
            )
        if upper_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Class_upper_cardinality"),
                Element(value=name.value + ".upper_cardinality"),
                upper_cardinality
            )
            self.instantiate_link(
                Element(value="Class_upper_cardinality_link"),
                Element(value=name.value + ".upper_cardinality_link"),
                name,
                Element(value=name.value + ".upper_cardinality")
            )

    def create_class_attribute(self, class_name: String, name: String, optional: Boolean = Element(value=False)):
        # create attribute
        element_name = Element(value=f"{class_name.value}_{name.value}")
        element_link_name = Element(value=f"{class_name.value}_{name.value}_link")
        self.instantiate(Element(value="Attribute"), element_name)
        self.instantiate_link(Element(value="AttributeLink"), element_link_name, class_name, element_name)
        # set attribute's attributes
        attr_name_name = Element(value=f"{class_name.value}_{name.value}.name")
        attr_optional_name = Element(value=f"{class_name.value}_{name.value}.optional")
        attr_name_link_name = Element(value=f"{class_name.value}_{name.value}.name_link")
        attr_optional_link_name = Element(value=f"{class_name.value}_{name.value}.optional_link")
        self.instantiate_value(Element(value="Attribute_name"), attr_name_name, name)
        self.instantiate_value(Element(value="Attribute_optional"), attr_optional_name, optional)
        self.instantiate_link(Element(value="Attribute_name_link"), attr_name_link_name, element_name, attr_name_name)
        self.instantiate_link(Element(value="Attribute_optional_link"), attr_optional_link_name, element_name, attr_optional_name)

    def create_association(self, source_class_name: String, target_class_name: String, name: String,
                           source_lower_cardinality: Integer = Element(), target_lower_cardinality: Integer = Element(),
                           source_upper_cardinality: Integer = Element(), target_upper_cardinality: Integer = Element()
                           ):
        self.instantiate_link(Element(value="Association"), name, source_class_name, target_class_name)
        if source_lower_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Association_source_lower_cardinality"),
                Element(value=name.value + ".source_lower_cardinality"),
                source_lower_cardinality
            )
            self.instantiate_link(
                Element(value="Association_source_lower_cardinality_link"),
                Element(value=name.value + ".source_lower_cardinality_link"),
                name,
                Element(value=name.value + ".source_lower_cardinality")
            )
        if source_upper_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Association_source_upper_cardinality"),
                Element(value=name.value + ".source_upper_cardinality"),
                source_upper_cardinality
            )
            self.instantiate_link(
                Element(value="Association_source_upper_cardinality_link"),
                Element(value=name.value + ".source_upper_cardinality_link"),
                name,
                Element(value=name.value + ".source_upper_cardinality")
            )
        if target_lower_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Association_target_lower_cardinality"),
                Element(value=name.value + ".target_lower_cardinality"),
                target_lower_cardinality
            )
            self.instantiate_link(
                Element(value="Association_target_lower_cardinality_link"),
                Element(value=name.value + ".target_lower_cardinality_link"),
                name,
                Element(value=name.value + ".target_lower_cardinality")
            )
        if target_upper_cardinality.value is not None:
            self.instantiate_value(
                Element(value="Association_target_upper_cardinality"),
                Element(value=name.value + ".target_upper_cardinality"),
                target_upper_cardinality
            )
            self.instantiate_link(
                Element(value="Association_target_upper_cardinality_link"),
                Element(value=name.value + ".target_upper_cardinality_link"),
                name,
                Element(value=name.value + ".target_upper_cardinality")
            )

    def create_inheritance(self, parent_class_name: String, child_class_name: String):
        self.instantiate_link(
            Element(value="Inheritance"),
            Element(value=f"{child_class_name.value}_inherits_from_{parent_class_name.value}"),
            child_class_name,
            parent_class_name)
