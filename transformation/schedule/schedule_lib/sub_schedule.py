from typing import List, override, TYPE_CHECKING

from jinja2 import Template

from api.od import ODAPI
from . import DataNode
from .exec_node import ExecNode
from .funcs import not_visited, generate_dot_node, IdGenerator

if TYPE_CHECKING:
    from ..rule_scheduler import RuleScheduler


class ScheduleState:
    def __init__(self) -> None:
        self.end_gate: str = ""

class SubSchedule(ExecNode, DataNode):
    def __init__(self, scheduler: "RuleScheduler", file: str) -> None:
        self.schedule = scheduler._load_schedule(file, _main=False)
        self.scheduler = scheduler
        super().__init__()
        self.state: dict[int, ScheduleState] = {}

    @override
    def nextState(self, exec_id: int) -> tuple["ExecNode", str]:
        return self.next_node[self.get_state(exec_id).end_gate]

    @override
    def get_exec_input_gates(self) -> "List[ExecNode]":
        return self.schedule.start.get_exec_output_gates()

    @override
    def get_exec_output_gates(self) -> "List[ExecNode]":
        return [*self.schedule.end.get_exec_input_gates()]

    @override
    def get_data_input_gates(self) -> "List[ExecNode]":
        return self.schedule.start.get_data_output_gates()

    @override
    def get_data_output_gates(self) -> "List[ExecNode]":
        return self.schedule.end.get_data_input_gates()

    def get_state(self, exec_id) -> ScheduleState:
        return self.state[exec_id]

    @override
    def generate_stack_frame(self, exec_id: int) -> None:
        super().generate_stack_frame(exec_id)
        self.state[exec_id] = ScheduleState()

    @override
    def delete_stack_frame(self, exec_id: int) -> None:
        super().delete_stack_frame(exec_id)
        self.state.pop(exec_id)


    @override
    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        runstatus, result = self.scheduler._runner(
            od,
            self.schedule,
            port,
            IdGenerator.generate_exec_id(),
            {
                port: self.get_input_data(port, exec_id)
                for port, value in self.data_in.items()
                if value is not None and not value.empty(exec_id)
            },
        )
        if runstatus != 1:
            return runstatus, result
        self.get_state(exec_id).end_gate = result["exec_gate"]
        results_data = result["data_out"]
        for port, data in self.data_out.items():
            if port in results_data:
                self.data_out[port].replace(exec_id, results_data[port])
                DataNode.input_event(self, port, exec_id)
                continue

            if not data.empty(exec_id):
                data.clear(exec_id)
                DataNode.input_event(self, port, exec_id)
        return None

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": "rrrrrrrrrr",
                "ports_exec": (
                    self.get_exec_input_gates(),
                    self.get_exec_output_gates(),
                ),
                "ports_data": (
                    self.get_data_input_gates(),
                    self.get_data_output_gates(),
                ),
            }
        )
        super().generate_dot(nodes, edges, visited, template)
