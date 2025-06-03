import functools
from typing import TYPE_CHECKING, Callable, List, Generator

from api.od import ODAPI
from examples.schedule.RuleExecuter import RuleExecuter
from .exec_node import ExecNode
from .data_node import DataNode


class Print(ExecNode, DataNode):
    def __init__(self, label: str = "") -> None:
        ExecNode.__init__(self, out_connections=1)
        DataNode.__init__(self)
        self.label = label

    def execute(self, od: ODAPI) -> Generator | None:
        self.input_event(True)
        return None

    def input_event(self, success: bool) -> None:
        print(f"{self.label}{self.data_in.data}")

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=Print_{self.label.replace(":", "")}]")
        ExecNode.generate_dot(self, nodes, edges, visited)
        DataNode.generate_dot(self, nodes, edges, visited)