from typing import List, override, Type

from jinja2 import Template

from api.od import ODAPI
from transformation.schedule.rule_executor import RuleExecutor
from .exec_node import ExecNode
from .data_node import DataNode
from .funcs import not_visited, generate_dot_node

class Match(ExecNode, DataNode):
    def input_event(self, gate: str, exec_id: int) -> None:
        pass

    def __init__(self, label: str, n: int | float) -> None:
        super().__init__()
        self.label: str = label
        self.n: int = n
        self.rule = None
        self.rule_executer: RuleExecutor | None = None

    @override
    def nextState(self, exec_id: int) -> tuple[ExecNode, str]:
        return self.next_node["fail" if self.data_out["out"].empty(exec_id) else "success"]

    @staticmethod
    @override
    def get_exec_output_gates():
        return ["success", "fail"]

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        pivot = {}
        if self.data_in is not None:
            pivot = self.get_input_data("in", exec_id)[0]
        # TODO: remove this print
        print(f"matching: {self.label}\n\tpivot: {pivot}")
        self.store_data( exec_id,
            self.rule_executer.match_rule(od.m, self.rule, pivot=pivot), "out", self.n
        )
        return None

    def init_rule(self, rule, rule_executer):
        self.rule = rule
        self.rule_executer = rule_executer

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"match_{self.n}\n{self.label}",
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
