from services.base import Service, UUID
from state.base import State
from typing import Any, List


class SCD(Service):
    def __init__(self, model: UUID, state: State):
        super().__init__(model)
        self.state = state

    def create_class(self, name: str, abstract: bool, min_c: int, max_c: int):
        pass

    def create_association(self, name: str, source: str, target: str, src_min_c: int, src_max_c: int, tgt_min_c: int, tgt_max_c: int):
        pass

    def create_global_constraint(self, name: str):
        pass

    def create_attribute(self, name: str):
        pass

    def create_attribute_link(self, source: str, target: str, name: str, optional: bool):
        pass

    def create_model_ref(self, name: str, model: UUID):
        pass

    def create_inheritance(self, child: str, parent: str):
        pass

    def add_constraint(self, element: str, code: str):
        pass

    def list_elements(self):
        pass

    def delete_element(self, name: str):
        pass

    def update_class(self, name: str, abstract: bool, min_c: int, max_c: int):
        pass

    def update_association(self, name: str, src_min_c: int, src_max_c: int, tgt_min_c: int, tgt_max_c: int):
        pass

    def update_attribute_link(self, name: str, attribute_name: str, optional: bool):
        pass
