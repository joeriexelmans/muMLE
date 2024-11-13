from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.plantuml import renderer as plantuml
from api.od import ODAPI

from examples.semantics.operational.simulator import Simulator, RandomDecisionMaker, InteractiveDecisionMaker
from examples.woods import models, opsem_python, opsem_rulebased
from examples.woods.common import termination_condition, render_woods

from util import loader

state = DevState()
scd_mmm = bootstrap_scd(state) # Load meta-meta-model

### Load (meta-)models ###

woods_mm    = loader.parse_and_check(state, models.woods_mm_cs,           scd_mmm,     "MM")
woods_rt_mm = loader.parse_and_check(state, models.woods_rt_mm_cs,        scd_mmm,     "RT-MM")
woods_m     = loader.parse_and_check(state, models.woods_m_cs,            woods_mm,    "M")
woods_rt_m  = loader.parse_and_check(state, models.woods_rt_initial_m_cs, woods_rt_mm, "RT-M")

print()

rulebased_action_generator = opsem_rulebased.get_action_generator(state, woods_rt_mm)

sim = Simulator(
    # action_generator=opsem_python.get_valid_actions,
    # action_generator=opsem_python.get_all_actions,
    action_generator=rulebased_action_generator,
    # decision_maker=RandomDecisionMaker(seed=3),
    decision_maker=InteractiveDecisionMaker(),
    termination_condition=termination_condition,
    check_conformance=True,
    verbose=True,
    renderer=render_woods,
)

od = ODAPI(state, woods_rt_m, woods_rt_mm)

sim.run(od)
