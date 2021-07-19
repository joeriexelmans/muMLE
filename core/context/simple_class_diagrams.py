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
        pass

    def create_class_attribute(self, class_name: String, name: String, optional: Boolean = Element(value=False)):
        pass

    def create_association(self, source_class_name: String, target_class_name: String, name: String,
                           source_lower_cardinality: Integer = Element(), target_lower_cardinality: Integer = Element(),
                           source_upper_cardinality: Integer = Element(), target_upper_cardinality: Integer = Element()
                           ):
        pass

    def create_inheritance(self, parent_class_name: String, child_class_name: String):
        pass
