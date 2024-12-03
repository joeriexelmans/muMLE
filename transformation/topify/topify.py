from uuid import UUID
from transformation.rule import RuleMatcherRewriter
from transformation.ramify import ramify
from util.loader import load_rules
from util.timer import Timer
from concrete_syntax.textual_od.renderer import render_od

import os
THIS_DIR = os.path.dirname(__file__)

class Topifier:
    def __init__(self, state):
        self.state = state
        # meta-meta-model
        self.scd_mmm = UUID(state.read_value(state.read_dict(state.read_root(), "SCD")))
        self.scd_mmm_ramified = ramify(state, self.scd_mmm)
        self.matcher_rewriter = RuleMatcherRewriter(state, self.scd_mmm, self.scd_mmm_ramified)

        # topification is implemented via model transformation
        self.rules = load_rules(state,
            lambda rule_name, kind: f"{THIS_DIR}/rules/r_{rule_name}_{kind}.od",
            self.scd_mmm_ramified, ["create_top", "create_inheritance"],
            check_conformance=False,
        )

    # Given a class diagram, extend it with a "Top"-type, i.e., an (abstract) supertype of all types. The set of instances of the "Top" is always the set of all objects in the diagram.
    def topify_cd(self, cd: UUID):
        with Timer("topify_cd"):
            # 1. Execute rule 'create_top' once
            rule = self.rules["create_top"]
            match_set = list(self.matcher_rewriter.match_rule(cd, rule.lhs, rule.nacs, "create_top"))
            if len(match_set) != 1:
                raise Exception(f"Expected rule 'create_top' to match only once, instead got {len(match_set)} matches")
            lhs_match = match_set[0]
            cd, rhs_match = self.matcher_rewriter.exec_rule(cd, rule.lhs, rule.rhs, lhs_match, "create_top")

            # 2. Execute rule 'create_inheritance' as many times as possible
            rule = self.rules["create_inheritance"]

            # for match in self.matcher_rewriter.match_rule(cd, rule.lhs, rule.nacs, "create_inheritance"):
            #     self.matcher_rewriter.exec_rule(cd, rule.lhs, rule.rhs, match, "create_inheritance", in_place=True)
            #     render_od(self.state, cd, self.scd_mmm)

            while True:
                iterator = self.matcher_rewriter.match_rule(cd, rule.lhs, rule.nacs, "create_inheritance")
                # find first match, and re-start matching
                try:
                    lhs_match = iterator.__next__() # may throw StopIteration
                    cd, rhs_match = self.matcher_rewriter.exec_rule(cd, rule.lhs, rule.rhs, lhs_match, "create_inheritance")
                except StopIteration:
                    break # no more matches
            return cd