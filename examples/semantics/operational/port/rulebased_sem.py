### Operational Semantics - defined by rule-based model transformation ###

from concrete_syntax.textual_od.parser import parse_od
from transformation.rule import Rule, RuleMatcherRewriter, PriorityActionGenerator
from transformation.matcher import match_od
from util import loader

import os
THIS_DIR = os.path.dirname(__file__)

# kind: lhs, rhs, nac
get_filename = lambda rule_name, kind: f"{THIS_DIR}/rules/r_{rule_name}_{kind}.od"


def get_action_generator(state, rt_mm, rt_mm_ramified):
    matcher_rewriter = RuleMatcherRewriter(state, rt_mm, rt_mm_ramified)

    #############################################################################
    # TO IMPLEMENT: Full semantics as a set of rule-based model transformations #

    rules0_dict = loader.load_rules(state, get_filename, rt_mm_ramified,
        ["ship_sinks"] # <- list of rule_name of equal priority
    )
    rules1_dict = loader.load_rules(state, get_filename, rt_mm_ramified,
        ["ship_appears_in_berth"]
    )
    # rules2_dict = ...

    generator = PriorityActionGenerator(matcher_rewriter, [
        rules0_dict, # highest priority
        rules1_dict, # lower priority
        # rules2_dict, # lowest priority
    ])

    # TO IMPLEMENT: Full semantics as a set of rule-based model transformations #
    #############################################################################

    return generator




# The termination condition can also be specified as a pattern:
class TerminationCondition:
    def __init__(self, state, rt_mm_ramified):
        self.state = state
        self.rt_mm_ramified = rt_mm_ramified

        # TO IMPLEMENT: terminate simulation when the place 'served' contains 2 ships.

        ########################################
        # You should only edit the pattern below
        pattern_cs = """
            # Placeholder to make the termination condition never hold:
            :GlobalCondition {
                condition = `False`;
            }
        """
        # You should only edit the pattern above
        ########################################

        self.pattern = parse_od(state, pattern_cs, rt_mm_ramified)

    def __call__(self, od):
        for match in match_od(self.state, od.m, od.mm, self.pattern, self.rt_mm_ramified):
            # stop after the first match (no need to look for more matches):
            return "There are 2 ships served." # Termination condition statisfied
