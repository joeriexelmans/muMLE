import pprint
from typing import Generator, Callable
from uuid import UUID
import functools

from api.od import ODAPI
from concrete_syntax.common import indent
from transformation.matcher.mvs_adapter import match_od
from transformation.rewriter import rewrite
from transformation.cloner import clone_od

class Rule:
    def __init__(self, nacs: list[UUID], lhs: UUID, rhs: UUID):
        self.nacs = nacs
        self.lhs = lhs
        self.rhs = rhs


PP = pprint.PrettyPrinter(depth=4)

# Helper for executing NAC/LHS/RHS-type rules
class RuleMatcherRewriter:
    def __init__(self, state, mm: UUID, mm_ramified: UUID):
        self.state = state
        self.mm = mm
        self.mm_ramified = mm_ramified

    # Generates matches.
    # Every match is a dictionary with entries LHS_element_name -> model_element_name
    def match_rule(self, m: UUID, lhs: UUID, nacs: list[UUID], rule_name: str) -> Generator[dict, None, None]:
        lhs_matcher = match_od(self.state,
            host_m=m,
            host_mm=self.mm,
            pattern_m=lhs,
            pattern_mm=self.mm_ramified)

        try:
            # First we iterate over LHS-matches:
            for i, lhs_match in enumerate(lhs_matcher):

                nac_matched = False

                for nac in nacs:
                    # For every LHS-match, we see if there is a NAC-match:
                    nac_matcher = match_od(self.state,
                        host_m=m,
                        host_mm=self.mm,
                        pattern_m=nac,
                        pattern_mm=self.mm_ramified,
                        pivot=lhs_match) # try to "grow" LHS-match with NAC-match

                    try:
                        for j, nac_match in enumerate(nac_matcher):
                            # The NAC has at least one match
                            # (there could be more, but we know enough, so let's not waste CPU/MEM resources and proceed to next LHS match)
                            nac_matched = True
                            break
                    except Exception as e:
                        # The exception may originate from eval'ed condition-code in LHS or NAC
                        # Decorate exception with some context, to help with debugging
                        e.add_note(f"while matching NAC of '{rule_name}'")
                        raise

                    if nac_matched:
                        break

                if not nac_matched:
                    # There were no NAC matches -> yield LHS-match!
                    yield lhs_match


        except Exception as e:
            # The exception may originate from eval'ed condition-code in LHS or NAC
            # Decorate exception with some context, to help with debugging
            e.add_note(f"while matching LHS of '{rule_name}'")
            raise

    def exec_rule(self, m: UUID, lhs: UUID, rhs: UUID, lhs_match: dict, rule_name: str):
        cloned_m = clone_od(self.state, m, self.mm)
        try:
            rhs_match = rewrite(self.state,
                lhs_m=lhs,
                rhs_m=rhs,
                pattern_mm=self.mm_ramified,
                lhs_match=lhs_match,
                host_m=cloned_m,
                host_mm=self.mm)
        except Exception as e:
            # Make exceptions raised in eval'ed code easier to trace:
            e.add_note(f"while executing RHS of '{rule_name}'")
            raise

        return (cloned_m, rhs_match)


# Generator that yields actions in the format expected by 'Simulator' class
class ActionGenerator:
    def __init__(self, matcher_rewriter: RuleMatcherRewriter, rule_dict: dict[str, Rule]):
        self.matcher_rewriter = matcher_rewriter
        self.rule_dict = rule_dict

    def __call__(self, od: ODAPI):
        at_least_one_match = False
        for rule_name, rule in self.rule_dict.items():
            for lhs_match in self.matcher_rewriter.match_rule(od.m, rule.lhs, rule.nacs, rule_name):
                # We got a match!
                def do_action(od, rule, lhs_match, rule_name):
                    new_m, rhs_match = self.matcher_rewriter.exec_rule(od.m, rule.lhs, rule.rhs, lhs_match, rule_name)
                    msgs = [f"executed rule '{rule_name}'\n" + indent(PP.pformat(rhs_match), 6)]
                    return (ODAPI(od.state, new_m, od.mm), msgs)
                yield (
                    rule_name + '\n' + indent(PP.pformat(lhs_match), 6), # description of action
                    functools.partial(do_action, od, rule, lhs_match, rule_name) # the action itself (as a callback)
                )
                at_least_one_match = True
        return at_least_one_match

# Given a list of actions (in high -> low priority), will always yield the highest priority enabled actions.
class PriorityActionGenerator:
    def __init__(self, matcher_rewriter: RuleMatcherRewriter, rule_dicts: list[dict[str, Rule]]):
        self.generators = [ActionGenerator(matcher_rewriter, rule_dict) for rule_dict in rule_dicts]

    def __call__(self, od: ODAPI):
        for generator in self.generators:
            at_least_one_match = yield from generator(od)
            if at_least_one_match:
                return True
        return False

# class ForAllGenerator:
#     def __init__(self, matcher_rewriter: RuleMatcherRewriter, rule_dict: dict[str, Rule]):
#         self.matcher_rewriter = matcher_rewriter
#         self.rule_dict = rule_dict

#     def __call__(self, od: ODAPI):
#         matches = []
#         for rule_name, rule in self.rule_dict.items():
#             for lhs_match in self.matcher_rewriter.match_rule(od.m, rule.lhs, rule.nacs, rule_name):
#                 matches.append((rule_name, rule, lhs_match))
#         def do_action(matches):
#             pass
#         if len(matches) > 0:
#             yield (
#                 [rule_name for rule_name, _, _ in matches]
#             )
#             return True
#         return False