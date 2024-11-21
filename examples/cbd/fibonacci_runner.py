from state.devstate import DevState
from bootstrap.scd import bootstrap_scd

from api.od import ODAPI

from concrete_syntax.common import indent
from concrete_syntax.textual_od import renderer as od_renderer
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as make_plantuml_url
from concrete_syntax.graphviz.make_url import make_url as make_graphviz_url
from concrete_syntax.graphviz import renderer as graphviz

from transformation.ramify import ramify
from transformation.rule import RuleMatcherRewriter, ActionGenerator

from examples.semantics.operational import simulator

from util import loader
import models


state = DevState()
scd_mmm = bootstrap_scd(state)

print("Parsing models...")
mm, mm_rt, m, m_rt_initial = models.load_fibonacci(state, scd_mmm)
mm_rt_ramified = ramify(state, mm_rt)

# print("RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt)))

# print("RAMIFIED RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt_ramified)))

high_priority_rules, low_priority_rules = models.load_rules(state, mm_rt_ramified)

matcher_rewriter = RuleMatcherRewriter(state, mm_rt, mm_rt_ramified)

high_priority_actions = ActionGenerator(matcher_rewriter, high_priority_rules)
low_priority_actions = ActionGenerator(matcher_rewriter, low_priority_rules)

# yields the currently enabled actions
def generate_actions(od):
    at_least_one_match = yield from high_priority_actions(od)
    if not at_least_one_match:
        # Only if no other action is possible, can time advance:
        yield from low_priority_actions(od)

sim = simulator.Simulator(
    action_generator=generate_actions,
    # decision_maker=simulator.InteractiveDecisionMaker(auto_proceed=False),
    decision_maker=simulator.RandomDecisionMaker(seed=0),
    termination_condition=lambda od: "Time is up" if od.get_slot_value(od.get_all_instances("Clock")[0][1], "time") >= 10 else None,
    check_conformance=True,
    verbose=True,
    renderer=lambda od: od_renderer.render_od(state, od.m, od.mm, hide_names=False),
)

sim.run(ODAPI(state, m_rt_initial, mm_rt))
