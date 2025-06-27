import functools
from typing import List, Generator, override, Type

from jinja2 import Template

from api.od import ODAPI
from .exec_node import ExecNode
from .data_node import DataNode
from .data_node import Data
from .funcs import not_visited, generate_dot_node

class Loop(ExecNode, DataNode):
    def __init__(self) -> None:
        super().__init__()
        self.cur_data: Data = Data(self)

    @staticmethod
    @override
    def get_exec_output_gates():
        return ["it", "out"]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.cur_data.generate_stack_frame(exec_id)

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().delete_stack_frame(exec_id)
        self.cur_data.delete_stack_frame(exec_id)

    @override
    def nextState(self, exec_id: int) -> tuple[ExecNode, str]:
        return self.next_node["out" if self.data_out["out"].empty(exec_id) else "it"]

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        self.data_out["out"].clear(exec_id)

        if not self.cur_data.empty(exec_id):
            self.data_out["out"].append(exec_id, self.cur_data.pop(exec_id,0))
        DataNode.input_event(self, "out", exec_id)
        return None

    def input_event(self, gate: str, exec_id: int) -> None:
        self.cur_data.replace(exec_id, self.get_input_data(gate, exec_id))
        data_o = self.data_out["out"]
        if data_o.empty(exec_id):
            return
        data_o.clear(exec_id)
        DataNode.input_event(self, "out", exec_id)


    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"loop",
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
