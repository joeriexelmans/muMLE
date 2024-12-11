from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.plantuml.renderer import render_object_diagram, render_class_diagram
from concrete_syntax.plantuml.make_url import make_url
from api.od import ODAPI

from transformation.ramify import ramify
from transformation.topify.topify import Topifier
from transformation.merger import merge_models
from transformation.ramify import ramify
from transformation.rule import RuleMatcherRewriter, ActionGenerator

from util import loader

from examples.semantics.operational.simulator import Simulator, RandomDecisionMaker, InteractiveDecisionMaker
from examples.semantics.operational.port import models
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time
from examples.semantics.operational.port.renderer import render_port_textual, render_port_graphviz
from examples.petrinet.renderer import show_petri_net
from examples.semantics.operational import simulator

import os
import sys
THIS_DIR = os.path.dirname(__file__)

# get file contents as string
def read_file(filename):
    with open(THIS_DIR+'/'+filename) as file:
        return file.read()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print(f"  python {__file__} model.od")
        print("where `model.od` is a valid instance of Port+Petri-Net.")
        sys.exit(1)

    model_to_open = sys.argv[1]

    state = DevState()
    scd_mmm = bootstrap_scd(state)

    print('loading merged MM...')
    merged_mm = loader.parse_and_check(state, read_file("merged_mm.od"), scd_mmm, "merged_mm.od", 
        check_conformance=False, # no need to check conformance every time
    )

    print('ramifying...')
    ramified_merged_mm = ramify(state, merged_mm)

    print('loading petri net rules...')
    rules = loader.load_rules(state,
        lambda rule_name, kind: f"{THIS_DIR}/../../petrinet/operational_semantics/r_{rule_name}_{kind}.od",
        ramified_merged_mm,
        ["fire_transition"])

    print('loading model...')
    filename = f"{THIS_DIR}/{model_to_open}"
    with open(filename, "r") as file:
        model = loader.parse_and_check(state, file.read(), merged_mm, "model",
            check_conformance=False, # no need to check conformance every time
        )
        print('loaded', filename)

    print('ready!')

    matcher_rewriter = RuleMatcherRewriter(state, merged_mm, ramified_merged_mm)
    action_generator = ActionGenerator(matcher_rewriter, rules)

    def render(od):
        show_petri_net(od) # graphviz in web browser
        return renderer.render_od(state, od.m, od.mm) # text in terminal

    sim = simulator.Simulator(
        action_generator=action_generator,
        decision_maker=simulator.InteractiveDecisionMaker(auto_proceed=False),
        # decision_maker=simulator.RandomDecisionMaker(seed=0),
        renderer=render,
    )

    sim.run(ODAPI(state, model, merged_mm))
