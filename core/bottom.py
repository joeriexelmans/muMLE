from state.base import State, INTEGER, FLOAT, STRING, BOOLEAN, TYPE, NODE, EDGE
from core.element import Element, String


class Bottom:
    def __init__(self, state: State) -> None:
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
        element_edge = self.state.create_edge(model_root, element)
        # label edge with provided name
        element_label = self.state.create_nodevalue(name.value)
        if element_label is None:
            print(f"Warning: Invalid name {name.value}, element not created.")
            return
        self.state.create_edge(element_edge, element_label)
        # add ltm-bottom typing
        element_type = self.state.create_nodevalue(NODE)
        self.state.create_dict(element_label, TYPE, element_type)

    def add_value(self, model: Element, name: String, value: Element):
        type_map = {
            int: INTEGER,
            float: FLOAT,
            bool: BOOLEAN,
            str: STRING
        }
        model_root = self.state.read_dict(model.id, "Model")
        # create model element
        element = self.state.create_nodevalue(value.value)
        if element is None:
            print("Warning: Invalid value, value node not created.")
            return
        # connect to model root
        element_edge = self.state.create_edge(model_root, element)
        # label edge with provided name
        element_label = self.state.create_nodevalue(name.value)
        if element_label is None:
            print(f"Warning: Invalid name {name.value}, element not created.")
            return
        self.state.create_edge(element_edge, element_label)
        # add ltm-bottom typing
        element_type = self.state.create_nodevalue(type_map[type(value.value)])
        self.state.create_dict(element_label, TYPE, element_type)

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
        element_edge = self.state.create_edge(model_root, element)
        # label edge with provided name
        element_label = self.state.create_nodevalue(name.value)
        if element_label is None:
            print(f"Warning: Invalid name {name.value}, element not created.")
            return
        self.state.create_edge(element_edge, element_label)
        # add ltm-bottom typing
        element_type = self.state.create_nodevalue(EDGE)
        self.state.create_dict(element_label, TYPE, element_type)

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
