import abc
import random
import math
import functools
import sys

from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.common import indent
from concrete_syntax.textual_od.renderer import render_od
from transformation.cloner import clone_od
from api.od import ODAPI

from util.simulator import MinimalSimulator, DecisionMaker, RandomDecisionMaker, InteractiveDecisionMaker


class Simulator(MinimalSimulator):
    def __init__(self,
        action_generator,
        decision_maker: DecisionMaker,
        termination_condition=lambda od: None,
        check_conformance=True,
        verbose=True,
        renderer=lambda od: render_od(od.state, od.m, od.mm),
    ):
        super().__init__(
            action_generator=action_generator,
            decision_maker=decision_maker,
            termination_condition=lambda od: self.check_render_termination_condition(od),
            verbose=verbose,
        )
        self.check_conformance = check_conformance
        self.actual_termination_condition = termination_condition
        self.renderer = renderer

    def check_render_termination_condition(self, od):
        # A termination condition checker that also renders the model, and performs conformance check
        self._print("--------------")
        self._print(indent(self.renderer(od), 2))
        self._print("--------------")
        if self.check_conformance:
            conf = Conformance(od.state, od.m, od.mm)
            self._print(render_conformance_check_result(conf.check_nominal()))
            self._print()
            return self.actual_termination_condition(od)

def make_actions_pure(actions, od):
    # Copy model before modifying it
    def exec_pure(action, od):
        cloned_rt_m = clone_od(od.state, od.m, od.mm)
        new_od = ODAPI(od.state, cloned_rt_m, od.mm)
        msgs = action(new_od)
        return (new_od, msgs)

    for descr, action in actions:
        yield (descr, functools.partial(exec_pure, action, od))

def filter_valid_actions(pure_actions):
    result = {}
    def make_tuple(new_od, msgs):
        return (new_od, msgs)
    for name, callback in pure_actions:
        # print(f"attempt '{name}' ...", end='\r')
        (new_od, msgs) = callback()
        conf = Conformance(new_od.state, new_od.m, new_od.mm)
        errors = conf.check_nominal()
        # erase current line:
        # print("                                                                                ", end='\r')
        if len(errors) == 0:
            # updated RT-M is conform, we have a valid action:
            yield (name, functools.partial(make_tuple, new_od, msgs))
