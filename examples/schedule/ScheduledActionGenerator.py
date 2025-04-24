import importlib.util
import io
import os

from jinja2 import FileSystemLoader, Environment

from concrete_syntax.textual_od import parser as parser_od
from concrete_syntax.textual_cd import parser as parser_cd
from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from examples.petrinet.schedule import Schedule
from examples.schedule.generator import schedule_generator
from examples.schedule.schedule_lib import End, NullNode
from framework.conformance import Conformance, render_conformance_check_result
from state.devstate import DevState

class ScheduleActionGenerator:
    def __init__(self, rule_executer, schedulefile:str):
        self.rule_executer = rule_executer
        self.rule_dict = {}
        self.schedule: Schedule


        self.state = DevState()
        self.load_schedule(schedulefile)

    def load_schedule(self, filename):
        print("Loading schedule ...")
        scd_mmm = bootstrap_scd(self.state)
        with open("../schedule/models/scheduling_MM.od", "r") as f_MM:
            mm_cs = f_MM.read()
        with open(f"{filename}", "r") as f_M:
            m_cs = f_M.read()
        print("OK")

        print("\nParsing models")

        print(f"\tParsing meta model")
        scheduling_mm = parser_cd.parse_cd(
            self.state,
            m_text=mm_cs,
        )
        print(f"\tParsing '{filename}_M.od' model")
        scheduling_m = parser_od.parse_od(
            self.state,
            m_text=m_cs,
            mm=scheduling_mm
        )
        print(f"OK")

        print("\tmeta-meta-model a valid class diagram")
        conf = Conformance(self.state, scd_mmm, scd_mmm)
        print(render_conformance_check_result(conf.check_nominal()))
        print(f"Is our '{filename}_M.od' model a valid '{filename}_MM.od' diagram?")
        conf = Conformance(self.state, scheduling_m, scheduling_mm)
        print(render_conformance_check_result(conf.check_nominal()))
        print("OK")

        od = ODAPI(self.state, scheduling_m, scheduling_mm)
        g = schedule_generator(od)

        output_buffer = io.StringIO()
        g.generate_schedule(output_buffer)
        open(f"schedule.py", "w").write(output_buffer.getvalue())
        spec = importlib.util.spec_from_file_location("schedule", "schedule.py")
        scedule_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scedule_module)
        self.schedule = scedule_module.Schedule(self.rule_executer)
        self.load_matchers()

    def load_matchers(self):
        matchers = dict()
        for file in self.schedule.get_matchers():
            matchers[file] = self.rule_executer.load_match(file)
        self.schedule.init_schedule(matchers)

    def __call__(self, api: ODAPI):
        exec_op = self.schedule(api)
        yield from exec_op

    def termination_condition(self, api: ODAPI):
        if type(self.schedule.cur) == End:
            return "jay"
        if type(self.schedule.cur) == NullNode:
            return "RRRR"
        return None

    def generate_dot(self):
        env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))
        env.trim_blocks = True
        env.lstrip_blocks = True
        template_dot = env.get_template('schedule_dot.j2')

        nodes = []
        edges = []
        visit = set()
        self.schedule.generate_dot(nodes, edges, visit)
        print("Nodes:")
        print(nodes)
        print("\nEdges:")
        print(edges)

        with open("test.dot", "w") as f_dot:
            f_dot.write(template_dot.render({"nodes": nodes, "edges": edges}))