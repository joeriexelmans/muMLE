import functools
from typing import List, Type

from jinja2 import Template

from api.od import ODAPI
from .exec_node import ExecNode
from .data_node import DataNode
from .funcs import not_visited, generate_dot_node
from ..rule_executor import RuleExecutor

class Rewrite(ExecNode, DataNode):

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label
        self.rule = None
        self.rule_executor: RuleExecutor | None = None

    def init_rule(self, rule, rule_executer):
        self.rule = rule
        self.rule_executor = rule_executer

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        pivot = {}
        if self.data_in is not None:
            pivot = self.get_input_data("in", exec_id)[0]
        # TODO: remove print
        print(f"rewrite: {self.label}\n\tpivot: {pivot}")
        self.store_data( exec_id,
            self.rule_executor.rewrite_rule(od, self.rule, pivot=pivot), "out", 1
        )
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
                "label": "rewrite",
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
