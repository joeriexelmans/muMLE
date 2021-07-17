from state.base import INTEGER, FLOAT, BOOLEAN, STRING, TYPE, State
from core.element import Element, String


class BottomContext:
    def __init__(self, state: State, model: Element):
        self.state = state
        self.model = model

    def __enter__(self):
        return self

    def __exit__(self):
        pass

    def add_node(self, name: String):
        model_root = self.state.read_dict(self.model.id, "Model")
        # create model element
        element = self.state.create_node()
        # connect to model root
        self.state.create_dict(model_root, name.value, element)
        # confirm that element has been added to the model
        element_found = self.state.read_dict(model_root, name.value)
        if element_found is None:
            self.state.delete_node(element)
            print(f"Warning: Invalid name {name.value}, element not created.")
            return

    def add_value(self, name: String, value: Element):
        model_root = self.state.read_dict(self.model.id, "Model")
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

    def add_edge(self, name: String, source: String, target: String):
        model_root = self.state.read_dict(self.model.id, "Model")
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
        element_found = self.state.read_dict(model_root, name.value)
        if element_found is None:
            self.state.delete_edge(element)
            print(f"Warning: Invalid name {name.value}, element not created.")

    def delete_element(self, name: String):
        model_root = self.state.read_dict(self.model.id, "Model")
        element = self.state.read_dict(model_root, name.value)
        # could be both a node or an edge
        self.state.delete_node(element)
        self.state.delete_edge(element)

    def list_elements(self):
        def is_edge(element: str) -> bool:
            edge = self.state.read_edge(element)
            return edge is not None

        def value_type(value) -> str:
            mapping = {
                int: INTEGER,
                float: FLOAT,
                str: STRING,
                bool: BOOLEAN,
                tuple: TYPE
            }
            return mapping[type(value)][0]
        
        unsorted = []
        model_root = self.state.read_dict(self.model.id, "Model")
        for elem_edge in self.state.read_outgoing(model_root):
            # get element name
            label_edge, = self.state.read_outgoing(elem_edge)
            _, label_node = self.state.read_edge(label_edge)
            label = self.state.read_value(label_node)
            # find element bottom type
            _, elem = self.state.read_edge(elem_edge)
            if is_edge(elem):
                bottom_type = "Edge"
            else:
                # is_node
                elem_value = self.state.read_value(elem)
                if elem_value is None:
                    bottom_type = "Node"
                else:
                    bottom_type = value_type
            unsorted.append(f"{label} : {bottom_type}")
        for i in sorted(unsorted):
            print(i)
