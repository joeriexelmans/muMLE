import sys
import os
from uuid import UUID

from black.trans import Callable
from jinja2.runtime import Macro

from api.od import ODAPI
from jinja2 import Environment, FileSystemLoader


class schedule_generator:
    def __init__(self, odApi: ODAPI):
        self.env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            )
        )
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.template = self.env.get_template("schedule_template.j2")
        self.template_wrap = self.env.get_template("schedule_template_wrap.j2")
        self.api = odApi


        def _get_slot_value_default(item: UUID, slot: str, default):
            if slot in self.api.get_slots(item):
                return self.api.get_slot_value(item, slot)
            return default

        conn_data_event = {
            "Match": lambda item: False,
            "Rewrite": lambda item: False,
            "Modify": lambda item: True,
            "Merge": lambda item: True,
            "Loop": lambda item: True,
            "Action": lambda item: _get_slot_value_default(item, "event", False),
            "Print": lambda item: _get_slot_value_default(item, "event", False),
            "Store": lambda item: False,
            "Schedule": lambda item: False,
            "End": lambda item: False,
        }

        arg_map = {
            "Loop": (name_dict := lambda item: {"name": self.api.get_name(item)}),
            "Start": lambda item: {
                **name_dict(item),
                "ports_exec_out": eval(
                    self.api.get_slot_value_default(item, "ports_exec_out", "['out']")
                ),
                "ports_data_out": eval(
                    self.api.get_slot_value_default(item, "ports_data_out", "[]")
                ),
            },
            "End": lambda item: {
                **name_dict(item),
                "ports_exec_in": eval(
                    self.api.get_slot_value_default(item, "ports_exec_in", "['in']")
                ),
                "ports_data_in": eval(
                    self.api.get_slot_value_default(item, "ports_data_in", "[]")
                ),
            },
            "Rewrite": (
                file_dict := lambda item: {
                    **name_dict(item),
                    "file": self.api.get_slot_value(item, "file"),
                }
            ),
            "Match": lambda item: {
                **file_dict(item),
                "n": self.api.get_slot_value_default(item, "n", 'float("inf")'),
            },
            "Action": lambda item: {
                **name_dict(item),
                "ports_exec_in": self.api.get_slot_value_default(item, "ports_exec_in", ["in"]),
                "ports_exec_out": self.api.get_slot_value_default(item, "ports_exec_out", ["out"]),
                "ports_data_in": self.api.get_slot_value_default(item, "ports_data_in", []),
                "ports_data_out": self.api.get_slot_value_default(item, "ports_data_out", []),
                "action": repr(self.api.get_slot_value(item, "action")),
                "init": repr(
                    self.api.get_slot_value_default(item, "init", "")
                ),
            },
            "Modify": lambda item: {
                **name_dict(item),
                "rename": eval(self.api.get_slot_value_default(item, "rename", "{}")),
                "delete": eval(self.api.get_slot_value_default(item, "delete", "{}")),
            },
            "Merge": lambda item: {
                **name_dict(item),
                "ports_data_in": eval(
                    self.api.get_slot_value_default(item, "ports_data_in", "[]")
                ),
            },
            "Store": lambda item: {
                **name_dict(item),
                "ports": eval(self.api.get_slot_value_default(item, "ports", "[]")),
            },
            "Schedule": file_dict,
            "Print": lambda item: {
                **name_dict(item),
                "label": self.api.get_slot_value_default(item, "label", ""),
                "custom": self.api.get_slot_value_default(item, "custom", ""),
            },
            "Conn_exec": (
                conn_dict := lambda item: {
                    "name_from": self.api.get_name(self.api.get_source(item)),
                    "name_to": self.api.get_name(self.api.get_target(item)),
                    "from": self.api.get_slot_value_default(item, "from", 0),
                    "to": self.api.get_slot_value_default(item, "to", 0),
                }
            ),
            "Conn_data": lambda item: {
                **conn_dict(item),
                "event": conn_data_event[
                    self.api.get_type_name(target := self.api.get_target(item))
                ](target),
            },
        }
        self.macro_args = {
            tp: (macro, arg_map.get(tp))
            for tp, macro in self.template.module.__dict__.items()
            if type(macro) == Macro
        }

    def _render(self, item):
        type_name = self.api.get_type_name(item)
        macro, arg_gen = self.macro_args[type_name]
        return macro(**arg_gen(item))

    def _dfs(
        self, stack: list[UUID], get_links: Callable, get_next_node: Callable
    ) -> tuple[set[UUID], list[UUID]]:
        visited = set()
        connections = list()
        while len(stack) > 0:
            obj = stack.pop()
            if obj in visited:
                continue
            visited.add(obj)
            for conn in get_links(self.api, obj):
                connections.append(conn)
                stack.append(get_next_node(self.api, conn))
        return visited, connections

    def generate_schedule(self, stream=sys.stdout):
        start = self.api.get_all_instances("Start")[0][1]
        end = self.api.get_all_instances("End")[0][1]
        out = {
            "blocks": [],
            "blocks_name": [],
            "blocks_start_end": [],
            "exec_conn": [],
            "data_conn": [],
            "match_files": set(),
            "matchers": [],
            "start": self.api.get_name(start),
            "end": self.api.get_name(end),
        }

        stack = [start, end]
        exec_blocks, conn_exec = self._dfs(
            stack,
            lambda api, node: api.get_outgoing(node, "Conn_exec"),
            lambda api, conn: api.get_target(conn),
        )

        for name, p in self.api.get_all_instances("Print"):
            if self.api.has_slot(p, "event") and self.api.get_slot_value(p, "event"):
                exec_blocks.add(p)

        stack = list(exec_blocks)
        blocks, conn_data = self._dfs(
            stack,
            lambda api, node: api.get_incoming(node, "Conn_data"),
            lambda api, conn: api.get_source(conn),
        )

        for exec_c in conn_exec:
            out["exec_conn"].append(self._render(exec_c))

        for data_c in conn_data:
            out["data_conn"].append(self._render(data_c))

        for block in blocks:
            out["blocks_name"].append(self.api.get_name(block))
            if block in [start, end]:
                out["blocks_start_end"].append(self._render(block))
                continue
            out["blocks"].append(self._render(block))
            if self.api.is_instance(block, "Rule"):
                d = self.macro_args[self.api.get_type_name(block)][1](block)
                out["match_files"].add(d["file"])
                out["matchers"].append(d)

        print(self.template_wrap.render(out), file=stream)
