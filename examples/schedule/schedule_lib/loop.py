import functools
from random import choice
from typing import TYPE_CHECKING, Callable, List, Generator

from api.od import ODAPI
from examples.schedule.RuleExecuter import RuleExecuter
from .exec_node import ExecNode
from .data_node import DataNode
from .data_node import Data


class Loop(ExecNode, DataNode):
    def __init__(self, choice) -> None:
        ExecNode.__init__(self, out_connections=2)
        DataNode.__init__(self)
        self.choice: bool = choice
        self.cur_data: Data = Data(-1)

    def nextState(self) -> ExecNode:
        return self.next_state[not self.data_out.success]

    def execute(self, od: ODAPI) -> Generator | None:
        if self.cur_data.empty():
            self.data_out.clear()
            self.data_out.success = False
            DataNode.input_event(self, False)
            return None

        if self.choice:
            def select_data() -> Generator:
                for i in range(len(self.cur_data)):
                    yield f"choice: {self.cur_data[i]}", functools.partial(self.select_next,od, i)
            return select_data()
        else:
            self.select_next(od, -1)
        return None

    def input_event(self, success: bool) -> None:
        if (b := self.data_out.success) or success:
            self.cur_data.replace(self.data_in)
            self.data_out.clear()
            self.data_out.success = False
            if b:
                DataNode.input_event(self, False)

    def select_next(self,od: ODAPI, index: int) -> tuple[ODAPI, list[str]]:
        self.data_out.clear()
        self.data_out.append(self.cur_data.pop(index))
        DataNode.input_event(self, True)
        return (od, ["data selected"])

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=Loop]")
        ExecNode.generate_dot(self, nodes, edges, visited)
        DataNode.generate_dot(self, nodes, edges, visited)