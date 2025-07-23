import functools
from typing import TYPE_CHECKING, List, Callable, Generator

from api.od import ODAPI
from .exec_node import ExecNode

class End(ExecNode):
    def __init__(self) -> None:
        super().__init__(out_connections=1)

    def execute(self, od: ODAPI) -> Generator | None:
        return self.terminate(od)

    @staticmethod
    def terminate(od: ODAPI) -> Generator:
        yield f"end:", functools.partial(lambda od:(od, ""), od)

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=end]")