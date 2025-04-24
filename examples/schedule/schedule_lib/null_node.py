import functools
from symtable import Function
from typing import List, Callable, Generator

from api.od import ODAPI
from .singleton import Singleton

from .exec_node import ExecNode

class NullNode(ExecNode, metaclass=Singleton):
    def __init__(self):
        ExecNode.__init__(self, out_connections=0)

    def execute(self, od: ODAPI) -> Generator | None:
        raise Exception('Null node should already have terminated the schedule')

    @staticmethod
    def terminate(od: ODAPI):
        return None
        yield # verrrry important line, dont remove this unreachable code

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=Null]")