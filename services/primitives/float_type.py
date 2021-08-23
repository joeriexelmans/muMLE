from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom


class Float:
    def __init__(self, model: UUID, state: State):
        self.model = model
        self.bottom = Bottom(state)
        type_model_id_node, = self.bottom.read_outgoing_elements(state.read_root(), "Float")
        self.type_model = UUID(self.bottom.read_value(type_model_id_node))

    def create(self, value: float):
        if "float" in self.bottom.read_keys(self.model):
            instance, = self.bottom.read_outgoing_elements(self.model, "float")
            self.bottom.delete_element(instance)
        _instance = self.bottom.create_node(value)
        self.bottom.create_edge(self.model, _instance, "float")
        _type, = self.bottom.read_outgoing_elements(self.type_model, "Float")
        self.bottom.create_edge(_instance, _type, "Morphism")
