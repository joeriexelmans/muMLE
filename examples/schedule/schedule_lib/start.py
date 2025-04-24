from typing import TYPE_CHECKING, Callable, List, Any

from .funcs import generate_dot_wrap

from .exec_node import ExecNode


class Start(ExecNode):
    def __init__(self) -> None:
        ExecNode.__init__(self, out_connections=1)

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        if self.id in visited:
            return
        nodes.append(f"{self.id}[label=start]")
        super().generate_dot(nodes, edges, visited)