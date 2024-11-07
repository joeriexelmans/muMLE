from state.devstate import DevState
from bootstrap.scd import bootstrap_scd

from framework.conformance import Conformance, render_conformance_check_result

from concrete_syntax.common import indent
from concrete_syntax.textual_od import renderer as od_renderer
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as make_plantuml_url
from concrete_syntax.graphviz.make_url import make_url as make_graphviz_url
from concrete_syntax.graphviz import renderer as graphviz

from transformation.matcher.mvs_adapter import match_od
from transformation.rewriter import rewrite
from transformation.cloner import clone_od

import models

state = DevState()
scd_mmm = bootstrap_scd(state)

print("Parsing models...")
mm, mm_rt, m, m_rt_initial = models.get_fibonacci(state, scd_mmm)
mm_rt_ram, rules = models.get_rules(state, mm_rt)

# print("RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt)))


# print("RAMIFIED RT-MM")
# print(make_plantuml_url(plantuml.render_class_diagram(state, mm_rt_ram)))

m_rt = m_rt_initial

def get_matches():
    for rule_name, rule in rules.items():
        lhs = rule["lhs"]

        lhs_matcher = match_od(state,
            host_m=m_rt,
            host_mm=mm_rt,
            pattern_m=lhs,
            pattern_mm=mm_rt_ram)

        try:
            for i, lhs_match in enumerate(lhs_matcher):
                nac_matcher = match_od(state,
                    host_m=m_rt,
                    host_mm=mm_rt,
                    pattern_m=rule["nac"],
                    pattern_mm=mm_rt_ram,
                    pivot=lhs_match)

                try:
                    for j, nac_match in enumerate(nac_matcher):
                        break # there may be more NAC-matches, but we already now enough
                    else:
                        # We got a match!
                        yield (rule_name, lhs, rule["rhs"], lhs_match)
                except Exception as e:
                    # Make exceptions raised in eval'ed code easier to trace:
                    e.add_note(f"while matching NAC of '{rule_name}'")
                    raise

        except Exception as e:
            # Make exceptions raised in eval'ed code easier to trace:
            e.add_note(f"while matching LHS of '{rule_name}'")
            raise

while True:
    # print(make_graphviz_url(graphviz.render_object_diagram(state, m_rt, mm_rt)))
    cs = od_renderer.render_od(state, m_rt, mm_rt, hide_names=False)
    print(indent(cs, 6))
    conf = Conformance(state, m_rt, mm_rt)
    print(render_conformance_check_result(conf.check_nominal()))

    matches = list(get_matches())

    print(f"There are {len(matches)} matches.")
    if len(matches) == 0:
        break
    rule_name, lhs, rhs, lhs_match = matches[0]


                # txt = graphviz.render_package("Host", graphviz.render_object_diagram(state, m_rt, mm_rt))
                # txt += graphviz.render_package("LHS", graphviz.render_object_diagram(state, lhs, mm_rt_ram))
                # txt += graphviz.render_trace_match(state, lhs_match, lhs, m_rt, color="orange")
                # match_urls.append(make_graphviz_url(txt))

    print(f"executing rule '{rule_name}' ", lhs_match)

    # copy or will be overwritten in-place
    m_rt = clone_od(state, m_rt, mm_rt)
    rhs_match = dict(lhs_match)
    try:
        rewrite(state,
            lhs_m=lhs,
            rhs_m=rhs,
            pattern_mm=mm_rt_ram,
            name_mapping=rhs_match,
            host_m=m_rt,
            host_mm=mm_rt)
    except Exception as e:
        # Make exceptions raised in eval'ed code easier to trace:
        e.add_note(f"while executing RHS of '{rule_name}'")
        raise

    # import subprocess
    # subprocess.run(["firefox", "--new-window", *match_urls])

# get_actions(state, rules, m_rt_initial, mm_rt)