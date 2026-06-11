import io
import os
import uuid

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import json

from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance
from rule_executor import RuleExecutor
from state.devstate import DevState
from concrete_syntax.textual_od import parser as parser_od
from concrete_syntax.textual_cd import parser as parser_cd
from transformation.ramify import ramify
from typing import TYPE_CHECKING, Any
from helpers import get_module_path
from exceptions.conformance_exception import Conformance_Exception
from processModel import create_workflow, ProcessModel

if TYPE_CHECKING:
    from rt_process import RT_Process


class Process:
    def __init__(self, process_model_file: Path) -> None:
        def read_mm_file(filename):
            with open(get_module_path("Models", filename)) as file:
                return file.read()

        def get_process_model(file: Path):
            extension = file.suffix
            with open(file) as f:
                m = f.read()
            match extension:
                case ".wf" | ".json":
                    return create_workflow(json.loads(m)).to_class_diagram()
                case _:
                    return m

        process_model = get_process_model(process_model_file)

        mm_cs_s = read_mm_file("meta_models/MModel.md")
        mm_rt_s = mm_cs_s + "\n" + read_mm_file("meta_models/RTState.md")

        state = DevState()
        scd_mmm = bootstrap_scd(state)

        mm_rt = parser_cd.parse_cd(
            state,
            m_text=mm_rt_s,
        )
        m = parser_od.parse_od(state, m_text=process_model, mm=mm_rt)
        conf_err = Conformance(state, m, mm_rt).check_nominal()
        if len(conf_err) > 0:
            raise Conformance_Exception(conf_err)

        self.od = ODAPI(state, m, mm_rt)
        self.rt_init = self.od.get_all_instances("RTState")[0]

        eval_context = {"generate_id": lambda: str(uuid.uuid4())}

        self.rule_executor = RuleExecutor(
            state, mm_rt, ramify(state, mm_rt, prefix=""), eval_context=eval_context
        )
        self.rules = {
            name: self.rule_executor.load_match(get_module_path("models/rules", file))
            for name, file in [
                # ("running_init", "running_init.od"),
                # ("running", "running.od"),
                # ("running_create", "running_create.od"),
                # ("delete", "delete.od"),
                ("prev", "prev.od"),
                #
                ("action_next_states", "action_next_states.od"),
                ("action_next_states_sync", "action_next_states_sync.od"),
                ("create_running_token", "create_running_token.od"),
                ("action_input_data", "action_input_data.od"),
                ("action_input_data2", "action_input_data2.od"),
                #
                ("create_new_RTState", "create_new_RTState.od"),
                ("get_running", "get_running.od"),
                ("get_running_token", "get_running_token.od"),
                ("copy_running", "copy_running.od"),
                ("create_running", "create_running.od"),
                ("delete_running", "delete_running.od"),
                #
                ("copy_data", "copy_data.od"),
                ("get_data", "get_data.od"),
                ("create_data", "create_data.od"),

                ("get_flow_input_port", "get_flow_input_port.od"),
                ("get_flow_token", "get_flow_token.od"),

                ("delete", "delete.od"),
            ]
        }

    def generate_dot(self, filename: str) -> None:
        with open(os.getcwd() + "/" + filename, "w") as f_dot:
            self.generate_dot_model(f_dot)

    def generate_runtime_object(self, env_filename: str | Path, process_lib: Path, parameters= {}) -> any:
        from rt_process import RT_Process

        return RT_Process(self, env_filename, process_lib, parameters)

    def generate_dot_model(self, outstream) -> None:
        env = Environment(loader=FileSystemLoader(get_module_path("templates", "")))
        env.trim_blocks = True
        env.lstrip_blocks = True
        template_dot = env.get_template("model_dot.j2")

        nodes = {
            i: [
                {
                    "id": node.__hash__(),
                    "name": name,
                    "params": {
                        slot: self.od.get_slot_value(node, slot)
                        for slot in self.od.get_slots(node)
                    },
                }
                for name, node in self.od.get_all_instances(i)
            ]
            for i in ["Place", "Port"]
        }
        edges = {
            i: [
                {
                    "source": self.od.get_source(edge).__hash__(),
                    "target": self.od.get_target(edge).__hash__(),
                }
                for name, edge in self.od.get_all_instances(i)
            ]
            for i in [
                "Transition",
                "Data_flow",
                "Port_data_in",
                "Port_data_out",
                "Port_flow_in",
                "Port_flow_out",
            ]
        }
        # nodes = [f"{node.__hash__()}[label={name}]" for name, node in self.od.get_all_instances("Place")]
        # edges = [(self.od.get_source(edge).__hash__(), self.od.get_target(edge).__hash__()) for _, edge in self.od.get_all_instances("Transition")]

        print(template_dot.render(nodes=nodes, edges=edges), file=outstream)

    def _create_running_places(self, new_rt_model, places) -> list[dict[str, str]]:
        result = []
        for running in places:
            m = self.rule_executor.rewrite_rule(
                self.od,
                self.rules["create_running"],
                pivot={"p_running": running, "state": new_rt_model},
            ).__next__()
            port_data = {

                 self.od.get_slot_value(
                    self.od.get(i["in_port"]), "Name"
                ): eval(self.od.get_slot_value(self.od.get(i["data"]), "Value"))
                for rule in [self.rules["action_input_data"], self.rules["action_input_data2"]]
                for i in self.rule_executor.match_rule(
                    self.od,
                    rule,
                    pivot={"state": new_rt_model, "p_running": m["p_running"]},
                )
            }

            result.append(
                {
                    "Place": m["p_running"],
                    "Id": self.od.get_value(self.od.get(m["run_new.Id"])),
                    "Process": self.od.get_slot_value(
                        self.od.get(m["p_running"]), "Process"
                    ),
                    "Data": port_data,
                }
            )
        return result

    def _copy_data(self, rt_key, new_rt_model) -> None:
        data_objs = self.rule_executor.match_rule(
            self.od, self.rules["copy_data"], pivot={"state": rt_key}
        )
        for data in data_objs:
            self.rule_executor.rewrite_rule(
                self.od,
                self.rules["copy_data"],
                pivot={"data": data["data"], "state": new_rt_model},
            ).__next__()

    def __init_data(self, rt_key, new_rt_model, init_values: dict[tuple[str, str], Any]) -> None:
        data_objs = self.rule_executor.match_rule(
            self.od, self.rules["get_data"], pivot={"state": rt_key}
        )
        for data in data_objs:
            place_name = self.od.get_slot_value(self.od.get(data["place"]), "Name")
            port_name = self.od.get_slot_value(self.od.get(data["port"]), "Name")
            data.pop("RTconn")
            data["state"] = new_rt_model
            m = self.rule_executor.rewrite_rule(
                self.od,
                self.rules["create_data"],
                pivot=data,
            ).__next__()
            value = init_values.get((place_name, port_name), None)
            value = f"'{value}'" if type(value) == str else value.__str__()
            self.od.set_slot_value(self.od.get(m["new_data"]), "Value", value)

    def start(self, rt_key, init_values: dict[tuple[str, str], Any]) -> tuple[str, list[dict[str, str]]]:
        newRTModel = self.rule_executor.rewrite_rule(
            self.od, self.rules["create_new_RTState"], pivot={"rt_state_old": rt_key}
        ).__next__()["rt_state"]
        self.__init_data(rt_key, newRTModel, init_values)
        running_places = [
            state["p_running"]
            for state in self.rule_executor.match_rule(
                self.od, self.rules["get_running"], pivot={"state": rt_key}
            )
        ]
        return newRTModel, self._create_running_places(newRTModel, running_places)

    def get_running_states(self, rt_key) -> list[str]:
        return [
            m
            for m in self.rule_executor.match_rule(
                self.od, self.rules["running"], pivot={"state": rt_key}
            )
        ]

    def step(self, rt_key, state, process_id, ports, data) -> tuple[Any, list[dict[str, str]]]:
        # Create new RTState
        newRTModel = self.rule_executor.rewrite_rule(
            self.od, self.rules["create_new_RTState"], pivot={"rt_state_old": rt_key}
        ).__next__()["rt_state"]

        # Copy run tokens to new state
        tokens = self.rule_executor.match_rule(self.od, self.rules["get_running_token"], pivot={"state": rt_key})
        [self.rule_executor.rewrite_rule(self.od, self.rules["get_running_token"], pivot={"state": newRTModel, "port_running": token["port_running"]}).__next__() for token in tokens]
        # Copy run markers, add Run_Id,
        process_running = None
        running_places = self.rule_executor.match_rule(
            self.od, self.rules["get_running"], pivot={"state": rt_key}
        )
        for run in running_places:
            m = self.rule_executor.rewrite_rule(
                self.od,
                self.rules["copy_running"],
                pivot={
                    "p_running": run["p_running"],
                    "run.Id": run["run.Id"],
                    "state": newRTModel,
                },
            ).__next__()
            if self.od.get_value(self.od.get(m["run.Id"])) == process_id:
                process_running = m
                process_running.pop("run.Id")
        assert not (process_running is None), "Process does not exists"

        self._copy_data(rt_key, newRTModel)
        data_ports = self.rule_executor.match_rule(
            self.od, self.rules["get_data"], pivot={"state": newRTModel, "place": state}
        )
        for data_port in data_ports:
            port_name = self.od.get_slot_value(self.od.get(data_port["port"]), "Name")
            m = self.rule_executor.rewrite_rule(
                self.od,
                self.rules["create_data"],
                pivot=data_port,
            ).__next__()
            value = data.get(port_name, None)
            value = f"'{value}'" if type(value) == str else value.__str__()
            self.od.set_slot_value(self.od.get(m["new_data"]), "Value", value)

        # Remove finished Process
        self.rule_executor.rewrite_rule(
            self.od, self.rules["delete_running"], pivot=process_running
        ).__next__()

        running_places_async = [
            state["p_next"]
            for state in self.rule_executor.match_rule(
                self.od,
                self.rules["action_next_states"],
                pivot={"p_running": state},
                params={"port_names": ports, "sync": False},
            )
        ]
        running_places_sync = [
            state
            for state in self.rule_executor.match_rule(
                self.od,
                self.rules["action_next_states"],
                pivot={"p_running": state},
                params={"port_names": ports, "sync": True},
            )
        ]
        [
            self.rule_executor.rewrite_rule(
                self.od,
                self.rules["create_running_token"],
                pivot={**match, "state": newRTModel},
                params={"sync": True},
            ).__next__()
            for match in running_places_sync
        ]
        for place in running_places_sync:
            sufficient_tokens = True
            tokens = []
            for port in self.rule_executor.match_rule(self.od, self.rules["get_flow_input_port"], pivot={"place": place["p_next"]}):
                matches = [i for i in self.rule_executor.match_rule(self.od, self.rules["get_flow_token"], pivot={**port, "state": newRTModel})]
                if len(matches) == 0:
                    sufficient_tokens = False
                    break
                tokens.append(matches[0]["token"])
            if sufficient_tokens:
                self.rule_executor.rewrite_rule(self.od, self.rules["delete"], pivot={f"_{i}": t for i, t in enumerate(tokens)}).__next__()
                running_places_async.append(place["p_next"])

        return newRTModel, self._create_running_places(
            newRTModel, running_places_async
        )

    def visualise(self, RTModel, filename) -> None:
        env = Environment(loader=FileSystemLoader(get_module_path("templates", "")))
        env.trim_blocks = True
        env.lstrip_blocks = True
        template_dot = env.get_template("RTmodel_dot.j2")

        nodes = {tp: [] for tp in ["RTState"]}
        edges = {tp: [] for tp in ["Prev", "Running"]}

        rt_states = {RTModel}
        state = RTModel
        try:
            # pass
            rt_states = [i for i, _ in self.od.get_all_instances("RTState")]
            # while True:
            # prev = self.rule_executor.match_rule(self.od, self.rules["prev"], pivot={"state": state}).__next__()
            # rt_states.append(state:= prev["prev_state"])
        except StopIteration:
            pass

        def node_to_dict(node):
            node_id = self.od.get(node)
            return {
                "id": node_id.__hash__(),
                "name": node,
                "params": {
                    slot: self.od.get_slot_value(node_id, slot)
                    for slot in self.od.get_slots(node_id)
                },
            }

        def edge_to_dict(edge):
            edge_id = self.od.get(edge)
            return {
                "source": self.od.get_source(edge_id).__hash__(),
                "target": self.od.get_target(edge_id).__hash__(),
                "name": edge,
                "params": {
                    slot: self.od.get_slot_value(edge_id, slot)
                    for slot in self.od.get_slots(edge_id)
                },
            }

        nodes_extend = {field: set() for field in ["Port_data"]}
        edges_extend = {
            field: set() for field in ["Port_data_connect", "RT_data_connect"]
        }

        for rt_state in rt_states:
            nodes["RTState"].append(node_to_dict(rt_state))

            for match in self.rule_executor.match_rule(
                self.od, self.rules["get_data"], pivot={"state": rt_state}
            ):
                nodes_extend["Port_data"].add(match["data"])
                edges_extend["Port_data_connect"].add(match["Dconn"])
                edges_extend["RT_data_connect"].add(match["RTconn"])

            for run in self.od.get_outgoing(self.od.get(rt_state), "Running"):
                edges["Running"].append(edge_to_dict(self.od.get_name(run)))

        nodes = nodes | {
            category: [node_to_dict(node) for node in value]
            for category, value in nodes_extend.items()
        }

        edges = edges | {
            category: [edge_to_dict(edge) for edge in value]
            for category, value in edges_extend.items()
        }

        for category_versioned in ["RTState", "Port_data"]:
            for versioned in nodes[category_versioned]:
                objs = {d["id"] for d in nodes[category_versioned]}
                for m in self.rule_executor.match_rule(
                    self.od, self.rules["prev"], pivot={"current": versioned["name"]}
                ):
                    if self.od.get(m["prev"]).__hash__() in objs:
                        edges["Prev"].append(edge_to_dict(m["prev_conn"]))

        outstream = io.StringIO()
        self.generate_dot_model(outstream)

        with open(os.getcwd() + "/" + filename, "w") as f_dot:
            f_dot.write(
                template_dot.render(
                    model=outstream.getvalue(), nodes=nodes, edges=edges
                )
            )

    def get_runtime_info(self, rt_key) -> dict[str, list[dict[str, Any]]]:
        info = {
            "Running": [
                {"state": i["p_running"]}
                for i in self.rule_executor.match_rule(
                    self.od, self.rules["get_running"], pivot={"state": rt_key}
                )
            ]
        }
        return info

    def is_finished(self, rt_key) -> bool:
        try:
            self.rule_executor.match_rule(self.od, self.rules["get_running"], pivot={"state": rt_key}).__next__()
            return False
        except StopIteration:
            return True

    def get_data_state(self, rt_key) -> dict[tuple[str, str], Any]:
        return {(self.od.get_slot_value(self.od.get(i["place"]), "Name"),
          self.od.get_value(self.od.get(i["port.Name"]))): eval(self.od.get_slot_value(self.od.get(i["data"]), "Value")) for i in
         self.rule_executor.match_rule(self.od, self.rules["get_data"], pivot={"state": rt_key})
                    }