import re

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from util import loader
from transformation.rule import RuleMatcherRewriter
from transformation.ramify import ramify
from concrete_syntax.graphviz import renderer as graphviz
from concrete_syntax.graphviz.make_url import make_url
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as plant_make_url
from api.od import ODAPI
import os
from os import listdir
from os.path import isfile, join
import importlib.util
from util.module_to_dict import module_to_dict
from examples.ftg_pm_pt import help_functions

from examples.ftg_pm_pt.ftg_pm_pt import FtgPmPt



class FtgPmPtRunner:

    def __init__(self, model: FtgPmPt, composite_linkage: dict | None = None):
        self.model = model
        self.ram_mm = ramify(self.model.state, self.model.meta_model)
        self.rules = self.load_rules()
        self.packages = None
        self.composite_linkage = composite_linkage

    def load_rules(self):
        return loader.load_rules(
            self.model.state,
            lambda rule_name, kind: os.path.join(
                os.path.dirname(__file__),
                f"operational_semantics/r_{rule_name}_{kind}.od"
            ),
            self.ram_mm,
            ["connect_process_trace", "trigger_ctrl_flow", "exec_activity", "exec_composite_activity"]
        )

    def set_packages(self, packages: str | dict, is_path: bool):
        if not is_path:
            self.packages = packages
            return

        self.packages = self.parse_packages(packages)

    def parse_packages(self, packages_path: str) -> dict:
        return self.collect_functions_from_packages(packages_path, packages_path)

    def collect_functions_from_packages(self, base_path, current_path):
        functions_dict = {}

        for entry in listdir(current_path):
            entry_path = join(current_path, entry)

            if isfile(entry_path) and entry.endswith(".py"):
                module_name = self.convert_path_to_module_name(base_path, entry_path)
                module = self.load_module_from_file(entry_path)

                for func_name, func in module_to_dict(module).items():
                    functions_dict[f"{module_name}.{func_name}"] = func

            elif not isfile(entry_path):
                nested_functions = self.collect_functions_from_packages(base_path, entry_path)
                functions_dict.update(nested_functions)

        return functions_dict

    @staticmethod
    def convert_path_to_module_name(base_path, file_path):
        return file_path.replace(base_path, "").replace(".py", "").replace("/", "")

    @staticmethod
    def load_module_from_file(file_path):
        spec = importlib.util.spec_from_file_location("", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def create_matcher(self):
        packages = module_to_dict(help_functions)

        if self.packages:
            packages.update({ "packages": self.packages })

        if self.composite_linkage:
            packages.update({ "composite_linkage": self.composite_linkage })

        matcher_rewriter = RuleMatcherRewriter(
            self.model.state, self.model.meta_model, self.ram_mm, eval_context=packages
        )
        return matcher_rewriter

    def visualize_model(self):
        print(make_url(graphviz.render_object_diagram(self.model.state, self.model.model, self.model.meta_model)))
        print(plant_make_url(plantuml.render_object_diagram(self.model.state, self.model.model, self.model.meta_model)))

    @staticmethod
    def __extract_artefact_info(od, pt_art):
        """Extract artefact metadata and data."""
        data = od.get_slot_value(pt_art, "data")
        pm_art = od.get_name(od.get_target(od.get_outgoing(pt_art, "pt_BelongsTo")[0]))
        has_prev_version = bool(od.get_outgoing(pt_art, "pt_PrevVersion"))
        is_last_version = not od.get_incoming(pt_art, "pt_PrevVersion")
        return {
            "Artefact Name": pm_art,
            "Data": data,
            "Has previous version": has_prev_version,
            "Is last version": is_last_version
        }

    def __extract_inputs(self, od, event_node):
        """Extract all consumed artefacts for an event."""
        return [
            self.__extract_artefact_info(od, od.get_source(consumes))
            for consumes in od.get_incoming(event_node, "pt_Consumes")
        ]

    def __extract_outputs(self, od, event_node):
        """Extract all produced artefacts for an event."""
        return [
            self.__extract_artefact_info(od, od.get_target(produces))
            for produces in od.get_outgoing(event_node, "pt_Produces")
        ]

    @staticmethod
    def to_snake_case(experiment_type):
        # Finds uppercase letters that are not at the start of the string.
        # Example: AtomicExperiment -> atomic_experiment
        return re.sub(r'(?<!^)(?=[A-Z])', '_', experiment_type).lower()

    def run(self, debug_flag: bool = False):
        matcher = self.create_matcher()

        rule_performed = True
        while rule_performed:

            # Loop over all the rules first in order priority
            for i, (rule_name, rule) in enumerate(self.rules.items()):
                rule_performed = False

                result = matcher.exec_on_first_match(
                    self.model.model, rule, rule_name, in_place=True
                )

                # If the rule cannot be executed go to the next rule
                if not result:
                    continue

                rule_performed = True
                self.model.model, lhs_match, _ = result

                if debug_flag:
                    print(f"Match: {lhs_match}")
                    self.visualize_model()

                # If a rule is performed, break and start loping over the rules from the beginning
                break