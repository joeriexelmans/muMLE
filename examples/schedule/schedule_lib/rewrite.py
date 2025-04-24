import functools
from typing import List, Callable, Generator

from api.od import ODAPI
from .exec_node import ExecNode
from .data_node import DataNode
from ..RuleExecuter import RuleExecuter


class Rewrite(ExecNode, DataNode):
    def __init__(self, label: str) -> None:
        ExecNode.__init__(self, out_connections=1)
        DataNode.__init__(self)
        self.label = label
        self.rule = None
        self.rule_executer : RuleExecuter

    def init_rule(self, rule, rule_executer):
        self.rule = rule
        self.rule_executer= rule_executer

    def execute(self, od: ODAPI) -> Generator | None:
        yield "ghello", functools.partial(self.rewrite, od)

    def rewrite(self, od):
        print("rewrite" + self.label)
        pivot = {}
        if self.data_in is not None:
            pivot = self.get_input_data()[0]
        self.store_data(self.rule_executer.rewrite_rule(od.m, self.rule, pivot=pivot), 1)
        return ODAPI(od.state, od.m, od.mm),[f"rewrite {self.label}\n\tpivot: {pivot}\n\t{"success" if self.data_out.success else "failure"}\n"]

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=R_{self.label.split("/")[-1]}]")
        ExecNode.generate_dot(self, nodes, edges, visited)
        DataNode.generate_dot(self, nodes, edges, visited)