import functools
import pprint

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd

from api.od import ODAPI

from concrete_syntax.common import indent
from concrete_syntax.textual_od import renderer as od_renderer
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as make_plantuml_url
from concrete_syntax.graphviz.make_url import make_url as make_graphviz_url
from concrete_syntax.graphviz import renderer as graphviz

from transformation.matcher.mvs_adapter import match_od
from transformation.rewriter import rewrite
from transformation.cloner import clone_od

from examples.semantics.operational import simulator

import models


def match_rule(rule_name, od: ODAPI, lhs, nac):
    lhs_matcher = match_od(state,
        host_m=od.m,
        host_mm=od.mm,
        pattern_m=lhs,
        pattern_mm=mm_rt_ram)

    try:
        for i, lhs_match in enumerate(lhs_matcher):
            nac_matcher = match_od(state,
                host_m=od.m,
                host_mm=od.mm,
                pattern_m=nac,
                pattern_mm=mm_rt_ram,
                pivot=lhs_match)

            try:
                for j, nac_match in enumerate(nac_matcher):
                    break # there may be more NAC-matches, but we already now enough -> proceed to next lhs_match
                else:
                    yield lhs_match # got match
            except Exception as e:
                # Make exceptions raised in eval'ed code easier to trace:
                e.add_note(f"while matching NAC of '{rule_name}'")
                raise

    except Exception as e:
        # Make exceptions raised in eval'ed code easier to trace:
        e.add_note(f"while matching LHS of '{rule_name}'")
        raise

def exec_action(rule_name, od: ODAPI, lhs, rhs, lhs_match):
    # copy these, will be overwritten in-place
    cloned_m = clone_od(state, od.m, od.mm)
    rhs_match = dict(lhs_match)

    try:
        rewrite(state,
            lhs_m=lhs,
            rhs_m=rhs,
            pattern_mm=mm_rt_ram,
            lhs_name_mapping=rhs_match,
            host_m=cloned_m,
            host_mm=od.mm)
    except Exception as e:
        # Make exceptions raised in eval'ed code easier to trace:
        e.add_note(f"while executing RHS of '{rule_name}'")
        raise

    print("Updated match:\n" + indent(pp.pformat(rhs_match), 6))

    return (ODAPI(state, cloned_m, od.mm), [f"executed rule '{rule_name}'"])

pp = pprint.PrettyPrinter(depth=4)

def attempt_rules(od: ODAPI, rule_dict):
    at_least_one_match = False
    for rule_name, rule in rule_dict.items():
        for lhs_match in match_rule(rule_name, od, rule["lhs"], rule["nac"]):
            # We got a match!
            yield (rule_name + '\n' + indent(pp.pformat(lhs_match), 6),
                functools.partial(exec_action,
                    rule_name, od, rule["lhs"], rule["rhs"], lhs_match))
            at_least_one_match = True
    return at_least_one_match

def get_actions(od: ODAPI):
    # transformation schedule
    rule_advance_time = rules["advance_time"]
    rules_not_advancing_time = { rule_name: rule for rule_name, rule in rules.items() if rule_name != "advance_time" }
    
    at_least_one_match = yield from attempt_rules(od, rules_not_advancing_time)
    if not at_least_one_match:
        yield from attempt_rules(od, {"advance_time": rule_advance_time})



state = DevState()
scd_mmm = bootstrap_scd(state)

print("Parsing models...")
mm, mm_rt, m, m_rt_initial = models.get_fibonacci(state, scd_mmm)
mm_rt_ram, rules = models.get_rules(state, mm_rt)

# print("RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt)))

# print("RAMIFIED RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt_ram)))

sim = simulator.Simulator(
    action_generator=get_actions,
    # decision_maker=simulator.InteractiveDecisionMaker(auto_proceed=False),
    decision_maker=simulator.RandomDecisionMaker(seed=0),
    termination_condition=lambda od: "Time is up" if od.get_slot_value(od.get_all_instances("Clock")[0][1], "time") >= 10 else None,
    check_conformance=True,
    verbose=True,
    renderer=lambda od: od_renderer.render_od(state, od.m, od.mm, hide_names=False),
)

sim.run(ODAPI(state, m_rt_initial, mm_rt))
