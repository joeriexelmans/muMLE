from state.base import State
from core.element import Element, String


class Manager:
    def __init__(self, state: State):
        self.state = state

    def new_model(self, name: String, type_model_name: String) -> Element:
        root = self.state.read_root()
        mm_bottom = self.state.read_dict(root, type_model_name.value)
        if mm_bottom is None:
            print(f"Error: Invalid type model name {type_model_name.value}. Model not created.")
            return Element()
        bottom = self.state.create_nodevalue(name.value)
        if bottom is None:
            print(f"Error: Invalid model name {name.value}. Model not created.")
            return Element()
        self.state.create_dict(root, name.value, bottom)
        self.state.create_dict(bottom, "Model", self.state.create_node())
        self.state.create_dict(bottom, "Metamodel", mm_bottom)
        return Element(id=bottom)

    def get_model(self, name: String) -> Element:
        root = self.state.read_root()
        model = self.state.read_dict(root, name.value)
        if model is None:
            print(f"Error: Cannot find model with name {name.value}.")
            return Element()
        return Element(id=model)

    def rename_model(self, name: String, new_name: String):
        root = self.state.read_root()
        name_used = self.state.read_dict_edge(root, new_name.value)
        if name_used:
            print(f"Error: Model with name {new_name.value} already exists. Please use another name.")
            return
        mode_edge = self.state.read_dict_edge(root, name.value)
        if mode_edge is None:
            print(f"Error: Cannot find model with name {name.value}.")
            return
        _,  model_node = self.state.read_edge(mode_edge)
        self.state.create_dict(root, new_name.value, model_node)
        created = self.state.read_dict_edge(root, new_name.value)
        if created is None:
            print(f"Error: Invalid model name {new_name.value}. Model not renamed.")
        else:
            self.state.delete_edge(mode_edge)

    def delete_model(self, name: String):
        root = self.state.read_root()
        model = self.state.read_dict(root, name.value)
        if model is None:
            print(f"Error: No model found for name {name.value}.")
        else:
            self.state.delete_node(model)

    def list_models(self):
        unsorted = []
        for edge in self.state.read_outgoing(self.state.read_root()):
            _, model = self.state.read_edge(edge)
            metamodel = self.state.read_dict(model, "Metamodel")
            unsorted.append(f"{self.state.read_value(model)} : {self.state.read_value(metamodel)}")
        for x in sorted(unsorted):
            print(x)
