from typing import List, override, Type

from jinja2 import Template

from api.od import ODAPI
from . import DataNode
from .exec_node import ExecNode
from .funcs import not_visited, generate_dot_node

class EndState:
    def __init__(self) -> None:
        self.end_gate: str = ""

class End(ExecNode, DataNode):
    @override
    def input_event(self, gate: str, exec_id: int) -> None:
        pass

    def __init__(self, ports_exec: List[str], ports_data: List[str]) -> None:
        self.ports_exec = ports_exec
        self.ports_data = ports_data
        super().__init__()
        self.state: dict[int, EndState] = {}

    @override
    def get_exec_input_gates(self):
        return self.ports_exec

    @staticmethod
    @override
    def get_exec_output_gates():
        return []

    @override
    def get_data_input_gates(self):
        return self.ports_data

    @staticmethod
    @override
    def get_data_output_gates():
        return []

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        state = self.get_state(exec_id)
        state.end_gate = port
        return 1, {"exec_gate": state.end_gate, "data_out": {port: data.get_data(exec_id) for port, data in self.data_in.items()}}

    def get_state(self, exec_id) -> EndState:
        return self.state[exec_id]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state[exec_id] = EndState()

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().delete_stack_frame(exec_id)
        self.state.pop(exec_id)

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": "end",
                "ports_exec": (
                    self.get_exec_input_gates(),
                    self.get_exec_output_gates(),
                ),
                "ports_data": (
                    self.get_data_input_gates(),
                    self.get_data_output_gates(),
                ),
            }
        )
