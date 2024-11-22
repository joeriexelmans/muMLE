from uuid import UUID
from transformation.rule import RuleMatcherRewriter
from transformation.ramify import ramify
from util.loader import load_rules

import os
THIS_DIR = os.path.dirname(__file__)

# Given a class diagram, extend it (in-place) with a "Top"-type, i.e., an (abstract) supertype of all types. The set of instances of the "Top" is always the set of all objects in the diagram.
def topify_cd(state, cd: UUID):
    # meta-meta-model
    scd_mmm = UUID(state.read_value(state.read_dict(state.read_root(), "SCD")))

    scd_mmm_ramified = ramify(state, scd_mmm)

    matcher_rewriter = RuleMatcherRewriter(state, scd_mmm, scd_mmm_ramified)
    
    # topification is implemented via model transformation
    rules = load_rules(state,
        lambda rule_name, kind: f"{THIS_DIR}/rules/r_{rule_name}_{kind}.od",
        scd_mmm_ramified, ["create_top", "create_inheritance"])

    # 1. Execute rule 'create_top' once
    rule = rules["create_top"]
    match_set = list(matcher_rewriter.match_rule(cd, rule.lhs, rule.nacs, "create_top"))
    if len(match_set) != 1:
        raise Exception(f"Expected rule 'create_top' to match only once, instead got {len(match_set)} matches")
    lhs_match = match_set[0]
    cd, rhs_match = matcher_rewriter.exec_rule(cd, rule.lhs, rule.rhs, lhs_match, "create_top")

    # 2. Execute rule 'create_inheritance' as many times as possible
    rule = rules["create_inheritance"]
    while True:
        iterator = matcher_rewriter.match_rule(cd, rule.lhs, rule.nacs, "create_inheritance")
        # find first match, and re-start matching
        try:
            lhs_match = iterator.__next__() # may throw StopIteration
            cd, rhs_match = matcher_rewriter.exec_rule(cd, rule.lhs, rule.rhs, lhs_match, "create_inheritance")
        except StopIteration:
            break # no more matches

    return cd