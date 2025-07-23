import sys
import os
import json
from uuid import UUID

from jinja2.runtime import Macro

from api.od import ODAPI
from jinja2 import Environment, FileSystemLoader, meta


class schedule_generator:
    def __init__(self, odApi:ODAPI):
        self.env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.template = self.env.get_template('schedule_template.j2')
        self.template_wrap = self.env.get_template('schedule_template_wrap.j2')
        self.api = odApi

        def get_slot_value_default(item: UUID, slot:str, default):
            if slot in self.api.get_slots(item):
                return self.api.get_slot_value(item, slot)
            return default

        name_dict = lambda item: {"name": self.api.get_name(item)}
        conn_dict = lambda item: {"name_from": self.api.get_name(self.api.get_source(item)),
                                  "name_to": self.api.get_name(self.api.get_target(item)),
                                  "gate_from": self.api.get_slot_value(item, "gate_from"),
                                  "gate_to": self.api.get_slot_value(item, "gate_to"),
                                  }

        conn_data_event = {"Match": lambda item: False,
                           "Rewrite": lambda item: False,
                           "Data_modify": lambda item: True,
                           "Loop": lambda item: True,
                           "Print": lambda item: get_slot_value_default(item, "event", False)
                           }
        conn_data_dict = lambda item: {"name_from": self.api.get_name(self.api.get_source(item)),
                                  "name_to": self.api.get_name(self.api.get_target(item)),
                                  "event": conn_data_event[self.api.get_type_name(target := self.api.get_target(item))](target)
                                  }
        rewrite_dict = lambda item: {"name": self.api.get_name(item),
                                  "file": self.api.get_slot_value(item, "file"),
                                  }
        match_dict = lambda item: {"name": self.api.get_name(item),
                                  "file": self.api.get_slot_value(item, "file"),
                                  "n": self.api.get_slot_value(item, "n") \
                                        if "n" in self.api.get_slots(item) else 'float("inf")'
                                  }
        data_modify_dict = lambda item: {"name": self.api.get_name(item),
                                  "dict": json.loads(self.api.get_slot_value(item, "modify_dict"))
                                  }
        loop_dict = lambda item: {"name": self.api.get_name(item),
                                  "choise": get_slot_value_default(item, "choise", False)}
        print_dict = lambda item: {"name": self.api.get_name(item),
                                   "label": get_slot_value_default(item, "label", "")}
        arg_map = {"Start": name_dict, "End": name_dict,
                   "Match": match_dict, "Rewrite": rewrite_dict,
                   "Data_modify": data_modify_dict, "Loop": loop_dict,
                   "Exec_con": conn_dict, "Data_con": conn_data_dict,
                   "Print": print_dict}
        self.macro_args = {tp: (macro, arg_map.get(tp)) for tp, macro in self.template.module.__dict__.items()
                                                if type(macro) == Macro}

    def _render(self, item):
        type_name = self.api.get_type_name(item)
        macro, arg_gen = self.macro_args[type_name]
        return macro(**arg_gen(item))

    def generate_schedule(self, stream = sys.stdout):
        start = self.api.get_all_instances("Start")[0][1]
        stack = [start]
        out = {"blocks":[], "exec_conn":[], "data_conn":[], "match_files":set(), "matchers":[], "start":self.api.get_name(start)}
        execBlocks = set()
        exec_conn = list()

        while len(stack) > 0:
            exec_obj = stack.pop()
            if exec_obj in execBlocks:
                continue
            execBlocks.add(exec_obj)
            for conn in self.api.get_outgoing(exec_obj, "Exec_con"):
                exec_conn.append(conn)
                stack.append(self.api.get_target(conn))

        stack = list(execBlocks)
        data_blocks = set()
        for name, p in self.api.get_all_instances("Print"):
            if "event" in (event := self.api.get_slots(p)) and event:
                stack.append(p)
                execBlocks.add(p)


        data_conn = set()
        while len(stack) > 0:
            obj = stack.pop()
            for data_c in self.api.get_incoming(obj, "Data_con"):
                data_conn.add(data_c)
                source = self.api.get_source(data_c)
                if not self.api.is_instance(source, "Exec") and \
                        source not in execBlocks and \
                        source not in data_blocks:
                    stack.append(source)
                    data_blocks.add(source)

        for exec_item in execBlocks:
            out["blocks"].append(self._render(exec_item))
            if self.api.is_instance(exec_item, "Rule"):
                d = self.macro_args[self.api.get_type_name(exec_item)][1](exec_item)
                out["match_files"].add(d["file"])
                out["matchers"].append(d)
        for exec_c in exec_conn:
            out["exec_conn"].append(self._render(exec_c))

        for data_c in data_conn:
            out["data_conn"].append(self._render(data_c))

        for data_b in data_blocks:
            out["blocks"].append(self._render(data_b))

        print(self.template_wrap.render(out), file=stream)





        # print("with open('test.dot', 'w') as f:", file=stream)
        # print(f"\tf.write({self.api.get_name(start)}.generate_dot())", file=stream)