from examples.schedule.RuleExecuter import RuleExecuter
from state.devstate import DevState
from api.od import ODAPI
from concrete_syntax.textual_od.renderer import render_od
from concrete_syntax.textual_od.renderer_jinja2 import render_od_jinja2
from bootstrap.scd import bootstrap_scd
from util import loader
from transformation.rule import RuleMatcherRewriter, ActionGenerator
from transformation.ramify import ramify
from examples.semantics.operational import simulator
from examples.petrinet.renderer import show_petri_net

from examples.schedule.ScheduledActionGenerator import *
from examples.schedule.RuleExecuter import *



if __name__ == "__main__":
    import os
    THIS_DIR = os.path.dirname(__file__)

    # get file contents as string
    def read_file(filename):
        with open(THIS_DIR+'/'+filename) as file:
            return file.read()


    state = DevState()
    scd_mmm = bootstrap_scd(state)

    # Read models from their files
    mm_cs           =         read_file('metamodels/mm_design.od')
    mm_rt_cs        = mm_cs + read_file('metamodels/mm_runtime.od')
    # m_cs            =         read_file('models/m_example_simple.od')
    # m_rt_initial_cs = m_cs +  read_file('models/m_example_simple_rt_initial.od')
    m_cs            =         read_file('models/m_example_mutex.od')
    m_rt_initial_cs = m_cs +  read_file('models/m_example_mutex_rt_initial.od')
    # m_cs            =         read_file('models/m_example_inharc.od')
    # m_rt_initial_cs = m_cs +  read_file('models/m_example_inharc_rt_initial.od')

    # Parse them
    mm           = loader.parse_and_check(state, mm_cs,           scd_mmm, "Petri-Net Design meta-model")
    mm_rt        = loader.parse_and_check(state, mm_rt_cs,        scd_mmm, "Petri-Net Runtime meta-model")
    m            = loader.parse_and_check(state, m_cs,            mm,      "Example model")
    m_rt_initial = loader.parse_and_check(state, m_rt_initial_cs, mm_rt,   "Example model initial state")

    mm_rt_ramified = ramify(state, mm_rt)

    rules = loader.load_rules(state,
        lambda rule_name, kind: f"{THIS_DIR}/operational_semantics/r_{rule_name}_{kind}.od",
        mm_rt_ramified,
        ["fire_transition"]) # only 1 rule :(

    # matcher_rewriter = RuleMatcherRewriter(state, mm_rt, mm_rt_ramified)
    # action_generator = ActionGenerator(matcher_rewriter, rules)

    matcher_rewriter2 = RuleExecuter(state, mm_rt, mm_rt_ramified)
    action_generator = ScheduleActionGenerator(matcher_rewriter2, f"models/schedule.od")

    def render_callback(od):
        show_petri_net(od)
        # return render_od(state, od.m, od.mm)
        return render_od_jinja2(state, od.m, od.mm)

    action_generator.generate_dot()

    sim = simulator.MinimalSimulator(
        action_generator=action_generator,
        decision_maker=simulator.InteractiveDecisionMaker(auto_proceed=False),
        # decision_maker=simulator.RandomDecisionMaker(seed=0),
        termination_condition=action_generator.termination_condition,
        # renderer=lambda od: render_od(state, od.m, od.mm),
    )

    sim.run(ODAPI(state, m_rt_initial, mm_rt))