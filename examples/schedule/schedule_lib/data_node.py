from typing import Any, Generator, List

from examples.schedule.schedule_lib.id_generator import IdGenerator
from .data import Data

class DataNode:
    def __init__(self) -> None:
        if not hasattr(self, 'id'):
            self.id = IdGenerator().generate_id()
        self.data_out : Data = Data(self)
        self.data_in: Data | None = None
        self.eventsub: list[DataNode] = list()

    def connect_data(self, data_node: "DataNode", eventsub=True) -> None:
        data_node.data_in = self.data_out
        if eventsub:
            self.eventsub.append(data_node)

    def store_data(self, data_gen: Generator, n: int) -> None:
        success: bool = self.data_out.store_data(data_gen, n)
        for sub in self.eventsub:
            sub.input_event(success)

    def get_input_data(self) -> list[dict[Any, Any]]:
        if not self.data_in.success:
            raise Exception("Invalid input data: matching has failed")
        data = self.data_in.data
        if len(data) == 0:
            raise Exception("Invalid input data: no data present")
        return data

    def input_event(self, success: bool) -> None:
        self.data_out.success = success
        for sub in self.eventsub:
            sub.input_event(success)

    def get_id(self) -> int:
        return self.id

    def generate_dot(self, nodes: List[str], edges: List[str], visited: set[int]) -> None:
        visited.add(self.id)
        if self.data_in is not None:
            edges.append(f"{self.data_in.get_super().get_id()} -> {self.get_id()} [color = green]")
            self.data_in.get_super().generate_dot(nodes, edges, visited)
        for sub in self.eventsub:
            sub.generate_dot(nodes, edges, visited)

