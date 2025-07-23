from typing import List, override

from jinja2 import Template

from transformation.schedule.schedule_lib.funcs import not_visited, generate_dot_node
from .data_node import DataNode


class Modify(DataNode):
    def __init__(self, rename: dict[str, str], delete: dict[str, str]) -> None:
        super().__init__()
        self.rename: dict[str, str] = rename
        self.delete: set[str] = set(delete)

    @override
    def input_event(self, gate: str, exec_id: int) -> None:
        data_i = self.get_input_data(gate, exec_id)
        if len(data_i):
            self.data_out["out"].clear(exec_id)
            for data in data_i:
                self.data_out["out"].append(exec_id,
                    {
                        self.rename.get(key, key): value
                        for key, value in data.items()
                        if key not in self.delete
                    }
                )
        else:
            if self.data_out["out"].empty(exec_id):
                return
        super().input_event("out", exec_id)

    @not_visited
    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": f"modify",
                "ports_data": (
                    self.get_data_input_gates(),
                    self.get_data_output_gates(),
                ),
            },
        )
        DataNode.generate_dot(self, nodes, edges, visited, template)
