from core.element import Element, String, Boolean
from state.base import State
from core.context.base import Context
from core.context.bottom import BottomContext


class GenericContext(Context):
    def __init__(self, state: State, model: Element, metamodel: Element):
        super().__init__(state, model, metamodel)
        self.bottom = BottomContext(state, model)

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def _type_exists(self, type_name: String, instantiate_link: bool) -> bool:
        metamodel_root = self.state.read_dict(self.metamodel.id, "Model")
        type_element = self.state.read_dict(metamodel_root, type_name.value)
        if type_element is None:
            return False
        else:
            element_is_edge = self.state.read_edge(type_element) is not None
            return element_is_edge == instantiate_link

    def instantiate(self, type_name: String, name: String):
        if not self._type_exists(type_name, instantiate_link=False):
            print(f"Attempting to instantiate element with invalid type: {type_name.value}")
        else:
            self.bottom.add_node(name)
            self.retype_element(name, type_name)

    def instantiate_value(self, type_name: String, name: String, value: Element):
        if not self._type_exists(type_name, instantiate_link=False):
            print(f"Attempting to instantiate element with invalid type: {type_name.value}")
        else:
            self.bottom.add_value(name, value.value)
            self.retype_element(name, type_name)

    def instantiate_link(self, type_name: String, name: String, source: String, target: String):
        if not self._type_exists(type_name, instantiate_link=True):
            print(f"Attempting to instantiate link with invalid type: {type_name.value}")
        else:
            self.bottom.add_edge(name, source, target)
            self.retype_element(name, type_name)

    def delete_element(self, name: String):
        self.bottom.delete_element(name)

    def verify(self):
        pass  # TODO: implement conformance check

    def list_elements(self):
        model_root = self.state.read_dict(self.model.id, "Model")
        unsorted = []
        for elem_edge in self.state.read_outgoing(model_root):
            # get element name
            label_edge, = self.state.read_outgoing(elem_edge)
            _, label_node = self.state.read_edge(label_edge)
            label = self.state.read_value(label_node)
            type_node = self.state.read_dict(label_node, "Type")
            type_name = self.state.read_value(type_node)
            unsorted.append(f"{label} : {type_name}")
        for i in sorted(unsorted):
            print(i)

    def retype_element(self, name: String, type_name: String):
        model_root = self.state.read_dict(self.model.id, "Model")
        element_edge = self.state.read_dict_edge(model_root, name.value)
        label_node_edge, = self.state.read_outgoing(element_edge)
        _, label_node = self.state.read_edge(label_node_edge)
        # create type name node
        type_name_node = self.state.create_nodevalue(type_name.value)
        if type_name_node is None:
            print("Warning: Invalid type name, element not retyped.")
        # remove any existing type node
        existing = self.state.read_dict(label_node, "Type")
        if existing is not None:
            self.state.delete_node(existing)
        # create new type node
        self.state.create_dict(label_node, "Type", type_name_node)
