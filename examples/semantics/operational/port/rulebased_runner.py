import urllib.parse

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser
from concrete_syntax.plantuml.renderer import render_object_diagram, render_class_diagram
from api.od import ODAPI

from transformation.ramify import ramify

from examples.semantics.operational.simulator import Simulator, RandomDecisionMaker, InteractiveDecisionMaker
from examples.semantics.operational.port import models
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time
from examples.semantics.operational.port.renderer import render_port_textual, render_port_graphviz

from examples.semantics.operational.port import rulebased_sem

state = DevState()
scd_mmm = bootstrap_scd(state) # Load meta-meta-model

### Load (meta-)models ###

def parse_and_check(m_cs: str, mm, descr: str):
    m = parser.parse_od(
        state,
        m_text=m_cs,
        mm=mm)
    conf = Conformance(state, m, mm)
    print(descr, "...", render_conformance_check_result(conf.check_nominal()))
    return m

port_mm    = parse_and_check(models.port_mm_cs,    scd_mmm,    "MM")
port_m     = parse_and_check(models.port_m_cs,     port_mm,    "M")
port_rt_mm = parse_and_check(models.port_rt_mm_cs, scd_mmm,    "RT-MM")
port_rt_m  = parse_and_check(models.port_rt_m_cs,  port_rt_mm, "RT-M")

print()

# print(render_class_diagram(state, port_rt_mm))

### Simulate ###

port_rt_mm_ramified = ramify(state, port_rt_mm)

rulebased_action_generator = rulebased_sem.get_action_generator(state, port_rt_mm, port_rt_mm_ramified)
termination_condition      = rulebased_sem.TerminationCondition(state, port_rt_mm_ramified)

sim = Simulator(
    action_generator=rulebased_action_generator,
    # decision_maker=RandomDecisionMaker(seed=2),
    decision_maker=InteractiveDecisionMaker(),
    termination_condition=termination_condition,
    check_conformance=True,
    verbose=True,
    # renderer=render_port_textual,
    # renderer=render_port_graphviz,
)

od = ODAPI(state, port_rt_m, port_rt_mm)

sim.run(od)
