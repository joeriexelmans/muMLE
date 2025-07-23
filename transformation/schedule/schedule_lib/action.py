from typing import List, override, Type

from jinja2 import Template

from api.od import ODAPI
from .funcs import not_visited, generate_dot_node
from .exec_node import ExecNode
from .data_node import DataNode

class ActionState:
    def __init__(self):
        self.var = {"output_gate": "out"}

class Action(ExecNode, DataNode):
    def __init__(
        self,
        ports_exec_in: list[str],
        ports_exec_out: list[str],
        ports_data_in: list[str],
        ports_data_out: list[str],
        code: str = "",
        init: str = "",
    ) -> None:
        self.gates: tuple[list[str], list[str], list[str], list[str]] = (ports_exec_in, ports_exec_out, ports_data_in, ports_data_out)
        super().__init__()
        self.state: dict[int, ActionState] = {}
        self.var_globals = {}
        self.code = code
        self.init = init

    @override
    def get_exec_input_gates(self) -> list[str]:
        return self.gates[0]

    @override
    def get_exec_output_gates(self) -> list[str]:
        return self.gates[1]

    @override
    def get_data_input_gates(self) -> list[str]:
        return self.gates[2]

    @override
    def get_data_output_gates(self) -> list[str]:
        return self.gates[3]

    @override
    def nextState(self, exec_id: int) -> tuple["ExecNode", str]:
        state = self.get_state(exec_id)
        return self.next_node[state.var["output_gate"]]

    def get_state(self, exec_id) -> ActionState:
        return self.state[exec_id]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state[exec_id] = (state := ActionState())
        if self.init:
            exec (self.init, {"var": state.var}, {"globals": self.var_globals})
    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state.pop(exec_id)

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        state = self.get_state(exec_id)
        exec(
            self.code,
            {
                "api": od,
                "var": state.var,
                "data_in": {port: value.get_data(exec_id) for port, value in self.data_in.items() if value is not None},
                "data_out": {port: value.get_data(exec_id) for port, value in self.data_out.items() if value is not None},
                "globals": self.var_globals,
            },
        )
        for gate, d in self.data_out.items():
            DataNode.input_event(self, gate, exec_id)
        return None

    def input_event(self, gate: str, exec_id: int) -> None:
        return

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"action",
                "ports_exec": (
                    self.get_exec_input_gates(),
                    self.get_exec_output_gates(),
                ),
                "ports_data": (
                    self.get_data_input_gates(),
                    self.get_data_output_gates(),
                ),
            },
        )
        ExecNode.generate_dot(self, nodes, edges, visited, template)
        DataNode.generate_dot(self, nodes, edges, visited, template)
