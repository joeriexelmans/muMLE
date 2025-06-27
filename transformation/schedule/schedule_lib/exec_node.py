from abc import abstractmethod
from api.od import ODAPI
from .node import Node


class ExecNode(Node):
    def __init__(self) -> None:
        super().__init__()

        from .null_node import NullNode
        self.next_node: dict[str, tuple[ExecNode, str]] = {}
        for port in self.get_exec_output_gates():
            self.next_node[port] = (NullNode(), "in")

    def nextState(self, exec_id: int) -> tuple["ExecNode", str]:
        return self.next_node["out"]

    @staticmethod
    def get_exec_input_gates():
        return ["in"]

    @staticmethod
    def get_exec_output_gates():
        return ["out"]

    def connect(self, next_state: "ExecNode", from_gate: str, to_gate: str) -> None:
        if from_gate not in self.get_exec_output_gates():
            raise Exception(f"from_gate {from_gate} is not a valid port")
        if to_gate not in next_state.get_exec_input_gates():
            raise Exception(f"to_gate {to_gate} is not a valid port")
        self.next_node[from_gate] = (next_state, to_gate)

    @abstractmethod
    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        return None
