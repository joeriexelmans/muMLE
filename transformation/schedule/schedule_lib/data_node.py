from abc import abstractmethod
from typing import Any, Generator, List, override

from jinja2 import Template

from .data import Data
from .funcs import generate_dot_edge
from .node import Node


class DataNodeState:
    def __init__(self) -> None:
        super().__init__()


class DataNode(Node):
    def __init__(self) -> None:
        super().__init__()
        self.eventsub: dict[str, list[tuple[DataNode, str]]] = {
            gate: [] for gate in self.get_data_output_gates()
        }
        self.data_out: dict[str, Data] = {
            name: Data(self) for name in self.get_data_output_gates()
        }
        self.data_in: dict[str, Data | None] = {
            name: None for name in self.get_data_input_gates()
        }

    @staticmethod
    def get_data_input_gates() -> List[str]:
        return ["in"]

    @staticmethod
    def get_data_output_gates() -> List[str]:
        return ["out"]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        for d in self.data_out.values():
            d.generate_stack_frame(exec_id)

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().delete_stack_frame(exec_id)
        for d in self.data_out.values():
            d.delete_stack_frame(exec_id)

    def connect_data(
        self, data_node: "DataNode", from_gate: str, to_gate: str, eventsub=True
    ) -> None:
        if from_gate not in self.get_data_output_gates():
            raise Exception(f"from_gate {from_gate} is not a valid port")
        if to_gate not in data_node.get_data_input_gates():
            raise Exception(f"to_gate {to_gate} is not a valid port")
        data_node.data_in[to_gate] = self.data_out[from_gate]
        if eventsub:
            self.eventsub[from_gate].append((data_node, to_gate))

    def store_data(self, exec_id, data_gen: Generator, port: str, n: int) -> None:
        self.data_out[port].store_data(exec_id, data_gen, n)
        for sub, gate in self.eventsub[port]:
            sub.input_event(gate, exec_id)

    def get_input_data(self, gate: str, exec_id: int) -> list[dict[Any, Any]]:
        data = self.data_in[gate]
        if data is None:
            return [{}]
        return data.get_data(exec_id)

    @abstractmethod
    def input_event(self, gate: str, exec_id: int) -> None:
        for sub, gate_sub in self.eventsub[gate]:
            sub.input_event(gate_sub, exec_id)

    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        for port, data in self.data_in.items():
            if data is not None:
                source = data.get_parent()
                generate_dot_edge(
                    source,
                    self,
                    edges,
                    template,
                    kwargs={
                        "prefix": "d",
                        "from_gate": [
                            port
                            for port, value in source.data_out.items()
                            if value == data
                        ][0],
                        "to_gate": port,
                        "color": "green",
                    },
                )
                data.get_parent().generate_dot(nodes, edges, visited, template)
        for gate_form, subs in self.eventsub.items():
            for sub, gate in subs:
                sub.generate_dot(nodes, edges, visited, template)
