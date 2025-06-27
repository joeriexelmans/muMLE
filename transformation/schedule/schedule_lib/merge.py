from typing import List, override, Type

from jinja2 import Template

from api.od import ODAPI
from transformation.schedule.rule_executor import RuleExecutor
from . import ExecNode
from .exec_node import ExecNode
from .data_node import DataNode, DataNodeState
from .funcs import not_visited, generate_dot_node

class Merge(DataNode):
    def __init__(self, ports: list[str]) -> None:
        self.in_data_ports = ports  # ports must be defined before super.__init__
        super().__init__()
        self.in_data_ports.reverse()

    @override
    def get_data_input_gates(self) -> list[str]:
        return self.in_data_ports

    @override
    def input_event(self, gate: str, exec_id: int) -> None:
        out = self.data_out["out"]
        b = (not out.empty(exec_id)) and (self.data_in[gate].empty(exec_id))
        out.clear(exec_id)
        if b:
            DataNode.input_event(self, "out", exec_id)
            return

        # TODO: only first element or all?
        if any(data.empty(exec_id) for data in self.data_in.values()):
            return
        d: dict[str, str] = dict()
        for gate in self.in_data_ports:
            for key, value in self.data_in[gate].get_data(exec_id)[0].items():
                d[key] = value
        out.append(exec_id, d)
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
                "label": f"merge",
                "ports_data": (
                    self.get_data_input_gates()[::-1],
                    self.get_data_output_gates(),
                ),
            },
        )
        DataNode.generate_dot(self, nodes, edges, visited, template)
