import functools
from typing import TYPE_CHECKING, Callable, List, Generator

from api.od import ODAPI
from examples.schedule.RuleExecuter import RuleExecuter
from .exec_node import ExecNode
from .data_node import DataNode


class Match(ExecNode, DataNode):
    def __init__(self, label: str, n: int | float) -> None:
        ExecNode.__init__(self, out_connections=2)
        DataNode.__init__(self)
        self.label: str = label
        self.n:int = n
        self.rule = None
        self.rule_executer : RuleExecuter

    def nextState(self) -> ExecNode:
        return self.next_state[not self.data_out.success]

    def execute(self, od: ODAPI) -> Generator | None:
        self.match(od)
        return None

    def init_rule(self, rule, rule_executer):
        self.rule = rule
        self.rule_executer = rule_executer

    def match(self, od: ODAPI) -> None:
        pivot = {}
        if self.data_in is not None:
            pivot = self.get_input_data()[0]
        print(f"matching: {self.label}\n\tpivot: {pivot}")
        self.store_data(self.rule_executer.match_rule(od.m, self.rule, pivot=pivot), self.n)

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=M_{self.label.split("/")[-1]}_{self.n}]")
        ExecNode.generate_dot(self, nodes, edges, visited)
        DataNode.generate_dot(self, nodes, edges, visited)