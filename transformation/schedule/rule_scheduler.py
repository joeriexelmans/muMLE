from __future__ import annotations

import importlib.util
import io
import os
import re
import sys

from pathlib import Path
from time import time
from typing import cast, TYPE_CHECKING

from jinja2 import FileSystemLoader, Environment

from concrete_syntax.textual_od import parser as parser_od
from concrete_syntax.textual_cd import parser as parser_cd
from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from transformation.schedule.rule_executor import RuleExecutor
from transformation.schedule.generator import schedule_generator
from transformation.schedule.models.eval_context import mm_eval_context
from transformation.schedule.schedule_lib import ExecNode, Start
from framework.conformance import Conformance, render_conformance_check_result, eval_context_decorator
from state.devstate import DevState
from examples.petrinet.renderer import render_petri_net_to_dot

from drawio2py import parser
from drawio2py.abstract_syntax import DrawIOFile, Edge, Vertex, Cell
from icecream import ic

from transformation.schedule.schedule_lib.funcs import IdGenerator

if TYPE_CHECKING:
    from transformation.schedule.schedule import Schedule


class RuleScheduler:
    __slots__ = (
        "rule_executor",
        "schedule_main",
        "loaded",
        "out",
        "verbose",
        "conformance",
        "directory",
        "eval_context",
        "_state",
        "_mmm_cs",
        "sub_schedules",
        "end_time",
    )

    def __init__(
        self,
        state,
        mm_rt,
        mm_rt_ramified,
        *,
        outstream=sys.stdout,
        verbose: bool = False,
        conformance: bool = True,
        directory: str = "",
        eval_context: dict[str, any] = None,
    ):
        self.rule_executor: RuleExecutor = RuleExecutor(state, mm_rt, mm_rt_ramified)
        self.schedule_main: Schedule | None = None
        self.out = outstream
        self.verbose: bool = verbose
        self.conformance: bool = conformance
        self.directory: Path = Path.cwd() / directory
        if eval_context is None:
            eval_context = {}
        self.eval_context: dict[str, any] = eval_context

        self.loaded: dict[str, dict[str, any]] = {"od": {}, "py": {}, "drawio": {}, "rules": {}}


        self._state = DevState()
        self._mmm_cs = bootstrap_scd(self._state)

        self.end_time = float("inf")
        self.sub_schedules = float("inf")

    def load_schedule(self, filename):
        return self._load_schedule(filename, _main=True) is not None


    def _load_schedule(self, filename: str, *, _main = True) -> Schedule | None:
        if filename.endswith(".drawio"):
            if (filename := self._generate_schedule_drawio(filename)) is None:
                return None

        if filename.endswith(".od"):
            if (filename := self._generate_schedule_od(filename)) is None:
                return None
        if filename.endswith(".py"):
            s = self._load_schedule_py(filename, _main=_main)
            return s

        raise Exception(f"Error unknown file: {filename}")

    def _load_schedule_py(self, filename: str, *, _main = True) -> "Schedule":
        if (s:= self.loaded["py"].get(filename, None)) is not None:
            return s

        spec = importlib.util.spec_from_file_location(filename, str(self.directory / filename))
        schedule_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schedule_module)
        self.loaded["py"][filename] = (s:= schedule_module.Schedule())
        if _main:
            self.schedule_main = s
        self.load_matchers(s)
        return s

    def _generate_schedule_od(self, filename: str) -> str | None:
        if (s:= self.loaded.get(("od", filename), None)) is not None:
            return s
        file = str(self.directory / filename)
        self._print("Generating schedule ...")
        with open(f"{os.path.dirname(__file__)}/models/scheduling_MM.od", "r") as f_MM:
            mm_cs = f_MM.read()
        try:
            with open(file, "r") as f_M:
                m_cs = f_M.read()
        except FileNotFoundError:
            self._print(f"File not found: {file}")
            return None

        self._print("OK\n\nParsing models\n\tParsing meta model")
        try:
            scheduling_mm = parser_cd.parse_cd(
                self._state,
                m_text=mm_cs,
            )
        except Exception as e:
            self._print(
                f"Error while parsing meta-model: scheduling_MM.od\n\t{e}"
            )
            return None
        self._print(f"\tParsing '{filename}' model")
        try:
            scheduling_m = parser_od.parse_od(
                self._state, m_text=m_cs, mm=scheduling_mm
            )
        except Exception as e:
            self._print(f"\033[91mError while parsing model: {filename}\n\t{e}\033[0m")
            return None
        if self.conformance:
            success = True
            self._print("OK\n\tmeta-meta-model a valid class diagram")
            conf_err = Conformance(
                self._state, self._mmm_cs, self._mmm_cs
            ).check_nominal()
            b = len(conf_err)
            success = success and not b
            self._print(
                f"\t\t{'\033[91m' if b else ''}{render_conformance_check_result(conf_err)}{'\033[0m' if b else ''}"
            )
            self._print(
                f"Is our '{filename}' model a valid 'scheduling_MM.od' diagram?"
            )
            conf_err = Conformance(
                self._state, scheduling_m, scheduling_mm, eval_context=mm_eval_context
            ).check_nominal()
            b = len(conf_err)
            success = success and not b
            self._print(
                f"\t\t{'\033[91m' if b else ''}{render_conformance_check_result(conf_err)}{'\033[0m' if b else ''}"
            )
            if not success:
                return None
        od = ODAPI(self._state, scheduling_m, scheduling_mm)
        g = schedule_generator(od)

        output_buffer = io.StringIO()
        g.generate_schedule(output_buffer)
        outfilename = f"{".".join(filename.split(".")[:-1])}.py"
        open(self.directory / outfilename, "w", encoding='utf-8').write(output_buffer.getvalue())
        self._print("Schedule generated")
        self.loaded[("od", filename)] = outfilename
        return outfilename

    def _print(self, *args) -> None:
        if self.verbose:
            print(*args, file=self.out)

    def load_matchers(self, schedule: "Schedule") -> None:
        matchers = dict()
        for file in schedule.get_matchers():
            if (r:= self.loaded.get(("rule", file), None)) is None:
                self.loaded[("rule", file)] = (r:= self.rule_executor.load_match(self.directory / file))
            matchers[file] = r
        schedule.init_schedule(self, self.rule_executor, matchers)

    def generate_dot(self, file: str) -> None:
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            )
        )
        env.trim_blocks = True
        env.lstrip_blocks = True
        template_dot = env.get_template("schedule_dot.j2")

        nodes = []
        edges = []
        visit = set()
        for schedule in self.loaded["py"].values():
            schedule.generate_dot(nodes, edges, visit, template_dot)
        with open(self.directory / file, "w") as f_dot:
            f_dot.write(template_dot.render(nodes=nodes, edges=edges))

    def run(self, model) -> tuple[int, str]:
        self._print("Start simulation")
        if 'pydevd' in sys.modules:
            self.end_time = time() + 1000
        else:
            self.end_time = time() + 10000
        return self._runner(model, self.schedule_main, "out", IdGenerator.generate_exec_id(), {})

    def _runner(self, model, schedule: Schedule, exec_port: str, exec_id: int, data: dict[str, any]) -> tuple[int, any]:
        self._generate_stackframe(schedule, exec_id)
        cur_node = schedule.start
        cur_node.run_init(exec_port, exec_id, data)
        while self.end_time > time():
            cur_node, port = cur_node.nextState(exec_id)
            termination_reason = cur_node.execute(port, exec_id, model)
            if termination_reason is not None:
                self._delete_stackframe(schedule, exec_id)
                return termination_reason

        self._delete_stackframe(schedule, exec_id)
        return -1, "limit reached"


    def _generate_stackframe(self, schedule: Schedule, exec_id: int) -> None:
        for node in schedule.nodes:
            node.generate_stack_frame(exec_id)

    def _delete_stackframe(self, schedule: Schedule, exec_id: int) -> None:
        for node in schedule.nodes:
            node.delete_stack_frame(exec_id)


    def _generate_schedule_drawio(self, filename:str) -> str | None:
        if (s:= self.loaded["drawio"].get(filename, None)) is not None:
            return s
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            )
        )
        env.trim_blocks = True
        env.lstrip_blocks = True
        template = env.get_template("schedule_muMLE.j2")
        main: bool = False

        node_map: dict[str, list[str | dict[str,str]]]
        id_counter: int
        def _get_node_id_map(elem: Cell) -> list[str | dict[str,str]]:
            nonlocal node_map, id_counter
            if (e_id := node_map.get(elem.id, None)) is None:
                e_id = [f"{re.sub(r'[^a-zA-Z1-9_]', '', elem.properties["name"])}_{id_counter}", {}]
                id_counter += 1
                node_map[elem.id] = e_id
            return e_id

        edges: list[tuple[tuple[str, str, str, str], tuple[str,str,str,str]]] = []
        def _parse_edge(elem: Edge):
            nonlocal edges
            try:
                edges.append((
                    (
                        _get_node_id_map(elem.source.parent.parent.parent)[0],
                        elem.source.properties["label"],
                        elem.source.properties["type"],
                        elem.source.parent.value
                    ),
                    (
                        _get_node_id_map(elem.target.parent.parent.parent)[0],
                        elem.target.properties["label"],
                        elem.target.properties["type"],
                        elem.target.parent.value
                    )
                ))
            except AttributeError as e:
                raise Exception(f"Missing attribute {e}")
            return

        def _parse_vertex(elem: Vertex):
            nonlocal edges
            try:
                elem_map = _get_node_id_map(elem)
                elem_map[1] = elem.properties
                properties = elem_map[1]
                properties.pop("label")
                properties.pop("name")
                properties.pop("placeholders")
                if properties.get("type") == "Schedule":
                    if not re.search(r'\.(py|od)$', properties["file"]):
                        properties["file"] = f"{filename}/{properties["file"]}.od"
            except AttributeError as e:
                raise Exception(f"Missing attribute {e}")
            return


        abstract_syntax: DrawIOFile = parser.Parser.parse(str(self.directory / filename))
        filename = filename.removesuffix(".drawio")
        (self.directory / filename).mkdir(parents=False, exist_ok=True)
        for page in abstract_syntax.pages:
            if page.name == "main":
                main = True
            if len(page.root.children) != 1:
                raise Exception(f"Only 1 layer allowed (keybind: ctr+shift+L)")
            edges = []
            id_counter = 1
            node_map = {}

            for element in page.root.children[0].children:
                match element.__class__.__name__:
                    case "Edge":
                        _parse_edge(cast(Edge, element))
                    case "Vertex":
                        _parse_vertex(cast(Vertex, element))
                        for elem in element.children[0].children:
                            if elem.__class__.__name__ == "Edge":
                                _parse_edge(cast(Edge, elem))
                        continue
                    case _:
                        raise Exception(f"Unexpected element: {element}")
            with open(self.directory / f"{filename}/{page.name}.od", "w", encoding="utf-8") as f:
                f.write(template.render(nodes=node_map, edges=edges))
        if main:
            self.loaded["drawio"][filename] = (filename_out := f"{filename}/main.od")
            return filename_out

        self._print("drawio schedule requires main page to automatically load.")
        return None
