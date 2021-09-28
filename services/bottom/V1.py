from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom as BottomV0


class Bottom:
    def __init__(self, model: UUID, state: State):
        type_model_id = state.read_dict(state.read_root(), "Bottom")
        self.type_model = UUID(state.read_value(type_model_id))
        self.model = model
        self.bottom = BottomV0(state)

    def create_node(self, name: str, value=None):

        if value is None:
            n = self.bottom.create_node()
        else:
            n = self.bottom.create_node(value)
        self.bottom.create_edge(self.model, n, label=name)

    def create_edge(self, name: str, source: str, target: str):
        try:
            src, = self.bottom.read_outgoing_elements(self.model, source)
        except ValueError:
            raise RuntimeError(f"No element named {source}")
        try:
            tgt, = self.bottom.read_outgoing_elements(self.model, source)
        except ValueError:
            raise RuntimeError(f"No element named {target}")
        e = self.bottom.create_edge(src, tgt)
        self.bottom.create_edge(self.model, e, label=name)

    def read_value(self, name: str):
        try:
            element, = self.bottom.read_outgoing_elements(self.model, name)
            return self.bottom.read_value(element)
        except ValueError:
            raise RuntimeError(f"No element named {name}")

    def read_edge_source(self, name: str):
        try:
            element, = self.bottom.read_outgoing_elements(self.model, name)
            return self.bottom.read_value(element)
        except ValueError:
            raise RuntimeError(f"No element named {name}")

    def read_edge_target(self, name: str):
        pass

    def delete_element(self, name: str):
        try:
            element, = self.bottom.read_outgoing_elements(self.model, name)
            self.bottom.delete_element(element)
        except ValueError:
            raise RuntimeError(f"No element named {name}")

    def list_elements(self):
        tm_names = {}
        for key in self.bottom.read_keys(self.type_model):
            element, = self.bottom.read_outgoing_elements(self.type_model, key)
            tm_names[element] = key
        unsorted = []
        for key in self.bottom.read_keys(self.model):
            element, = self.bottom.read_outgoing_elements(self.model, key)
            element_types = self.bottom.read_outgoing_elements(element, "Morphism")
            type_model_elements = self.bottom.read_outgoing_elements(self.type_model)
            element_type_node, = [e for e in element_types if e in type_model_elements]
            unsorted.append(f"{key} : {tm_names[element_type_node]}")
        return sorted(unsorted)

    def to_bottom(self):
        pass  # already encoded as bottom

    def from_bottom(self):
        pass  # already encoded as bottom

