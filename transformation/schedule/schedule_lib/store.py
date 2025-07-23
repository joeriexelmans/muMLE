from typing import List, override

from jinja2 import Template

from api.od import ODAPI
from .data import Data
from .exec_node import ExecNode
from .data_node import DataNode
from .funcs import not_visited, generate_dot_node

class StoreState:
    def __init__(self) -> None:
        self.last_port: str = "in"

class Store(ExecNode, DataNode):
    def __init__(self, ports: list[str]) -> None:
        self.ports = ports
        super().__init__()
        self.state: dict[int, StoreState] = {}
        self.cur_data: Data = Data(self)

    @override
    def get_exec_input_gates(self) -> list[str]:
        return [*self.ports, "in"]

    @override
    def get_exec_output_gates(self) -> list[str]:
        return [*self.ports, "out"]

    @override
    def get_data_input_gates(self) -> list[str]:
        return self.ports

    @override
    def nextState(self, exec_id: int) -> tuple[ExecNode, str]:
        return self.next_node[self.get_state(exec_id).last_port]

    @override
    def input_event(self, gate: str, exec_id: int) -> None:
        return

    def get_state(self, exec_id) -> StoreState:
        return self.state[exec_id]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state[exec_id] = StoreState()
        self.cur_data.generate_stack_frame(exec_id)

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state.pop(exec_id)
        self.cur_data.delete_stack_frame(exec_id)


    @override
    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        state = self.get_state(exec_id)
        if port == "in":
            self.data_out["out"].replace(exec_id, self.cur_data.get_data(exec_id))
            self.cur_data.clear(exec_id)
            DataNode.input_event(self, "out", True)
            state.last_port = "out"
            return None
        self.cur_data.extend(exec_id, self.get_input_data(port, exec_id))
        state.last_port = port
        return None

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"store",
                "ports_exec": (
                    self.get_exec_input_gates(),
                    self.get_exec_output_gates(),
                ),
                "ports_data": (
                    self.get_data_input_gates(),
                    self.get_data_output_gates(),
                ),
            },
        )
        ExecNode.generate_dot(self, nodes, edges, visited, template)
        DataNode.generate_dot(self, nodes, edges, visited, template)
