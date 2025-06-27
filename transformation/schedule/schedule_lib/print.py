from typing import List, override

from jinja2 import Template

from api.od import ODAPI
from transformation.schedule.schedule_lib.funcs import not_visited, generate_dot_node
from .exec_node import ExecNode
from .data_node import DataNode


class Print(ExecNode, DataNode):
    def __init__(self, label: str = "", custom: str = "") -> None:
        super().__init__()
        self.label = label

        if custom:
            template = Template(custom, trim_blocks=True, lstrip_blocks=True)
            self._print = (
                lambda self_, exec_id: print(template.render(data=self.get_input_data("in", exec_id)))
            ).__get__(self, Print)

    @staticmethod
    @override
    def get_data_output_gates():
        return []

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        self._print(exec_id)
        return

    @override
    def input_event(self, gate: str, exec_id: int) -> None:
        if not self.data_in[gate].empty(exec_id):
            self._print(exec_id)

    def _print(self, exec_id: int) -> None:
        print(f"{self.label}{self.get_input_data("in", exec_id)}")

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"print",
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
