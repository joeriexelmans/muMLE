from state.base import State
from core.element import Element, String


class Bottom:
    def __init__(self, state: State):
        self.state = state

    def create_model(self, name: String) -> Element:
        bottom = self.state.create_nodevalue(name.value)
        self.state.create_dict(bottom, "Model", self.state.create_node())
        return Element(id=bottom)

    def add_node(self, model: Element, name: String):
        model_root = self.state.read_dict(model.id, "Model")
        # create model element
        element = self.state.create_node()
        # connect to model root
        self.state.create_dict(model_root, name.value, element)
        # confirm that element has been added to the model
        element = self.state.read_dict(model_root, name.value)
        if element is None:
            self.state.delete_node(element)
            print(f"Warning: Invalid name {name.value}, element not created.")
            return

    def add_value(self, model: Element, name: String, value: Element):
        model_root = self.state.read_dict(model.id, "Model")
        # create model element
        element = self.state.create_nodevalue(value.value)
        if element is None:
            print("Warning: Invalid value, value node not created.")
            return
        # connect to model root
        self.state.create_dict(model_root, name.value, element)
        # confirm that element has been added to the model
        element_found = self.state.read_dict(model_root, name.value)
        if element_found is None:
            self.state.delete_node(element)
            print(f"Warning: Invalid name {name.value}, element not created.")
            return

    def add_edge(self, model: Element, name: String, source: String, target: String):
        model_root = self.state.read_dict(model.id, "Model")
        source_element = self.state.read_dict(model_root, source.value)
        if source_element is None:
            print(f"Warning: Unknown source element {source.value}, edge not created.")
            return
        target_element = self.state.read_dict(model_root, target.value)
        if target_element is None:
            print(f"Warning: Unknown target element {target.value}, edge not created.")
            return
        # create model element
        element = self.state.create_edge(source_element, target_element)
        # connect to model root
        self.state.create_dict(model_root, name.value, element)
        # confirm that element has been added to the model
        element = self.state.read_dict(model_root, name.value)
        if element is None:
            self.state.delete_edge(element)
            print(f"Warning: Invalid name {name.value}, element not created.")

    def get_element(self, model: Element, name: String) -> Element:
        model_root = self.state.read_dict(model.id, "Model")
        element = self.state.read_dict(model_root, name.value)
        if element is None:
            print(f"Warning: Unknown element {name.value}.")
            return Element()
        else:
            return Element(id=element, value=self.state.read_value(element))

    def delete_element(self, model: Element, name: String):
        model_root = self.state.read_dict(model.id, "Model")
        element = self.state.read_dict(model_root, name.value)
        # could be both a node or an edge
        self.state.delete_node(element)
        self.state.delete_edge(element)
