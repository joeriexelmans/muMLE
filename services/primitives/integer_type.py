from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom


class Integer:
    def __init__(self, model: UUID, state: State):
        self.model = model
        self.bottom = Bottom(state)
        type_model_id_node, = self.bottom.read_outgoing_nodes(state.read_root(), "Integer")
        self.type_model = UUID(self.bottom.read_value(type_model_id_node))

    def create(self, value: int):
        if "string" in self.bottom.read_keys(self.model):
            instance, = self.bottom.read_outgoing_nodes(self.model, "integer")
            self.bottom.delete_element(instance)
        _instance = self.bottom.create_edge(self.model, self.bottom.create_node(value), "integer")
        _type, = self.bottom.read_outgoing_nodes(self.type_model, "Integer")
        self.bottom.create_edge(_instance, _type, "Morphism")
