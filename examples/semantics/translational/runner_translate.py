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
from transformation.rule import RuleMatcherRewriter

from util import loader

from examples.semantics.operational.simulator import Simulator, RandomDecisionMaker, InteractiveDecisionMaker
from examples.semantics.operational.port import models
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time
from examples.semantics.operational.port.renderer import render_port_textual, render_port_graphviz
from examples.petrinet.renderer import render_petri_net

import os
THIS_DIR = os.path.dirname(__file__)

# get file contents as string
def read_file(filename):
    with open(THIS_DIR+'/'+filename) as file:
        return file.read()

if __name__ == "__main__":
    state = DevState()
    scd_mmm = bootstrap_scd(state)

    print('loading merged MM...')
    merged_mm = loader.parse_and_check(state, read_file("merged_mm.od"), scd_mmm, "merged_mm.od", 
        check_conformance=False, # no need to check conformance every time
    )

    print('ramifying...')
    ramified_merged_mm = ramify(state, merged_mm)

    ###################################
    # This is the main part you want to edit (by adding/changing the transformation rules)
    #  |   |   |
    #  V   V   V
    rule_names = [
        # high to low priority:
        "00_place2place",
        "10_conn2trans",

        # The above two rules create a bunch of PN places and PN transitions.
        # (with generic_links to the Port-elements)
        # One way to continue, is to create PN arcs between the places and transitions.
        # Or you can also just start from scratch, if you have a better idea :)
    ]
    # The script below will keep executing the first rule until it no longer matches, then the second rule, etc.
    ###################################


    print('loading rules...')
    rules = loader.load_rules(state,
        lambda rule_name, kind: f"{THIS_DIR}/rules/gen_pn/r_{rule_name}_{kind}.od",
        ramified_merged_mm,
        rule_names)

    print('loading model...')
    port_m_rt_initial = loader.parse_and_check(state, models.port_rt_m_cs, merged_mm, "Port-M-RT-initial",
        check_conformance=False, # no need to check conformance every time
    )

    print('ready!')

    port_m_rt = port_m_rt_initial
    matcher_rewriter = RuleMatcherRewriter(state, merged_mm, ramified_merged_mm)

    ###################################
    # Because the matching of many different rules can be slow,
    # this script will store intermediate snapshots each time
    # after having 'exhausted' a rule.
    # When re-running the script, the stored snapshots will be loaded
    # from disk instead of re-running the rules.
    # You can force re-running the rules (e.g., because you changed the rules)
    # by deleting the `snapshot_after_*` files.
    ###################################

    ###################################
    # You are allowed to edit the script below, but you don't have to.
    # Changes you may want to make:
    #  - outcomment the 'render_petri_net'-call (preventing popups)
    #  - if you really want to do something crazy,
    #     you can even write a script that uses the lower-level `match_od`/`rewrite` primitives...
    #  - ??
    ###################################

    for i, rule_name in enumerate(rule_names):
        filename = f"{THIS_DIR}/snapshot_after_{rule_name}.od"
        print("rule =", rule_name)
        rule = rules[rule_name]
        try:
            with open(filename, "r") as file:
                port_m_rt = parser.parse_od(state, file.read(), merged_mm)
                print('loaded', filename)
        except FileNotFoundError:
            # Fire every rule until it cannot match any longer:
            while True:
                result = matcher_rewriter.exec_on_first_match(port_m_rt, rule, rule_name,
                    in_place=True, # faster
                )
                if result == None:
                    print("  no matches")
                    break
                else:
                    port_m_rt, lhs_match, _ = result
                    print("  rewrote", lhs_match)
            txt = renderer.render_od(state, port_m_rt, merged_mm)
            with open(filename, "w") as file:
                file.write(txt)
                print('wrote', filename)
                render_petri_net(ODAPI(state, port_m_rt, merged_mm))

    ###################################
    # Once you have generated a Petri Net, you can execute the petri net:
    #
    #   python runner_exec_pn.py snapshot_after_XX_name_of_my_last_rule.od
    ###################################