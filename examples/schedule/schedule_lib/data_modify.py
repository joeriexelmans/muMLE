import functools
from typing import TYPE_CHECKING, Callable, List

from api.od import ODAPI
from examples.schedule.RuleExecuter import RuleExecuter
from .exec_node import ExecNode
from .data_node import DataNode


class DataModify(DataNode):
    def __init__(self, modify_dict: dict[str,str]) -> None:
        DataNode.__init__(self)
        self.modify_dict: dict[str,str] = modify_dict

    def input_event(self, success: bool) -> None:
        if success or self.data_out.success:
            self.data_out.data.clear()
            for data in self.data_in.data:
                self.data_out.append({self.modify_dict[key]: value for key, value in data.items() if key in self.modify_dict.keys()})
            DataNode.input_event(self, success)

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=modify]")
        super().generate_dot(nodes, edges, visited)
