from concrete_syntax.textual_od.renderer import render_od

import pprint
from typing import Generator, Callable, Any
from uuid import UUID
import functools

from api.od import ODAPI
from concrete_syntax.common import indent
from transformation.matcher import match_od
from transformation.rewriter import rewrite
from transformation.cloner import clone_od
from util.timer import Timer
from util.loader import parse_and_check

class RuleExecuter:
    def __init__(self, state, mm: UUID, mm_ramified: UUID, eval_context={}):
        self.state = state
        self.mm = mm
        self.mm_ramified = mm_ramified
        self.eval_context = eval_context

    # Generates matches.
    # Every match is a dictionary with entries LHS_element_name -> model_element_name
    def match_rule(self, m: UUID, lhs: UUID, *, pivot:dict[Any, Any]):
        lhs_matcher = match_od(self.state,
                               host_m=m,
                               host_mm=self.mm,
                               pattern_m=lhs,
                               pattern_mm=self.mm_ramified,
                               eval_context=self.eval_context,
                               pivot= pivot,
                               )
        return lhs_matcher

    def rewrite_rule(self, m: UUID, rhs: UUID, *, pivot:dict[Any, Any]):
        yield rewrite(self.state,
                rhs_m=rhs,
                pattern_mm=self.mm_ramified,
                lhs_match=pivot,
                host_m=m,
                host_mm=self.mm,
                eval_context=self.eval_context,
            )


    def load_match(self, file: str):
        with open(file, "r") as f:
            return parse_and_check(self.state, f.read(), self.mm_ramified, file)
