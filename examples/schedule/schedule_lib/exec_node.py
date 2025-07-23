from typing import TYPE_CHECKING, List, Callable, Generator
from api.od import ODAPI

from .id_generator import IdGenerator

class ExecNode:
    def __init__(self, out_connections: int = 1) -> None:
        from .null_node import NullNode
        self.next_state: list[ExecNode] = []
        if out_connections > 0:
            self.next_state = [NullNode()]*out_connections
        self.id: int = IdGenerator().generate_id()

    def nextState(self) -> "ExecNode":
        return self.next_state[0]

    def connect(self, next_state: "ExecNode", from_gate: int = 0, to_gate: int = 0) -> None:
        if from_gate >= len(self.next_state):
            raise IndexError
        self.next_state[from_gate] = next_state

    def execute(self, od: ODAPI) -> Generator | None:
        return None

    def get_id(self) -> int:
        return self.id

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        visited.add(self.id)
        for edge in self.next_state:
            edges.append(f"{self.id} -> {edge.get_id()}")
        for next in self.next_state:
            next.generate_dot(nodes, edges, visited)

