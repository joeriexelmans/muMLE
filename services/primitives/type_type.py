from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom


class Integer:
    def __init__(self, model: UUID, state: State):
        self.model = model
        self.bottom = Bottom(state)
        type_model_id_node, = self.bottom.read_outgoing_elements(state.read_root(), "Type")
        self.type_model = UUID(self.bottom.read_value(type_model_id_node))

    def create(self, value: tuple):
        if "string" in self.bottom.read_keys(self.model):
            instance, = self.bottom.read_outgoing_elements(self.model, "type")
            self.bottom.delete_element(instance)
        _instance = self.bottom.create_edge(self.model, self.bottom.create_node(value), "type")
        _type, = self.bottom.read_outgoing_elements(self.type_model, "Type")
        self.bottom.create_edge(_instance, _type, "Morphism")
