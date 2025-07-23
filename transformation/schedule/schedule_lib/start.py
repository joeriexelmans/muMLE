from typing import List, override

from jinja2 import Template

from . import DataNode
from .exec_node import ExecNode
from .funcs import not_visited, generate_dot_node

class StartState:
    def __init__(self) -> None:
        super().__init__()
        self.start_gate: str = ""

class Start(ExecNode, DataNode):
    def __init__(self, ports_exec: List[str], ports_data: List[str]) -> None:
        self.state: dict[int, StartState] = {}
        self.ports_exec = ports_exec
        self.ports_data = ports_data
        super().__init__()

    def run_init(self, gate: str, exec_id: int, data: dict[str, any]) -> None:
        state = self.get_state(exec_id)
        state.start_gate = gate
        for port, d in data.items():
            self.data_out[port].replace(exec_id, d)
            DataNode.input_event(self, port, exec_id)

    def nextState(self, exec_id: int) -> tuple["ExecNode", str]:
        state = self.get_state(exec_id)
        return self.next_node[state.start_gate]

    def get_state(self, exec_id) -> StartState:
        return self.state[exec_id]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state[exec_id] = StartState()

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state.pop(exec_id)

    @staticmethod
    @override
    def get_exec_input_gates():
        return []

    @override
    def get_exec_output_gates(self):
        return self.ports_exec

    @staticmethod
    @override
    def get_data_input_gates():
        return []

    @override
    def get_data_output_gates(self):
        return self.ports_data

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": "start",
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
        super().generate_dot(nodes, edges, visited, template)
