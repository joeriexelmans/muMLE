import abc
import random
import math
import functools
import sys

from framework.conformance import Conformance, render_conformance_check_result

from concrete_syntax.common import indent
from concrete_syntax.textual_od.renderer import render_od

class DecisionMaker:
    @abc.abstractmethod
    def __call__(self, actions):
        pass

class Simulator:
    def __init__(self,
        action_generator,
        decision_maker: DecisionMaker,
        termination_condition,
        check_conformance=True,
        verbose=True,
        renderer=lambda od: render_od(od.state, od.m, od.mm),
    ):
        self.action_generator = action_generator
        self.decision_maker = decision_maker
        self.termination_condition = termination_condition
        self.check_conformance = check_conformance
        self.verbose = verbose
        self.renderer = renderer

    def __print(self, *args):
        if self.verbose:
            print(*args)

    # Run simulation until termination condition satisfied
    def run(self, od):
        self.__print("Start simulation")
        step_counter = 0
        while True:
            self.__print("--------------")
            self.__print(indent(self.renderer(od), 4))
            self.__print("--------------")

            termination_reason = self.termination_condition(od)
            if termination_reason != None:
                self.__print(f"Termination condition satisfied.\nReason: {termination_reason}.")
                break

            actions = self.action_generator(od)

            chosen_action = self.decision_maker(actions)

            if chosen_action == None:
                self.__print(f"No enabled actions.")
                break

            (od, msgs) = chosen_action()
            self.__print(indent('\n'.join(f"▸ {msg}" for msg in msgs), 2))

            step_counter += 1

            if self.check_conformance:
                self.__print()
                conf = Conformance(od.state, od.m, od.mm)
                self.__print(render_conformance_check_result(conf.check_nominal()))
        self.__print(f"Executed {step_counter} steps.")
        return od


def filter_valid_actions(actions):
    result = {}
    def make_tuple(new_od, msgs):
        return (new_od, msgs)
    for name, callback in actions:
        print(f"attempt '{name}' ...", end='\r')
        (new_od, msgs) = callback()
        conf = Conformance(new_od.state, new_od.m, new_od.mm)
        errors = conf.check_nominal()
        # erase current line:
        print("                                                  ", end='\r')
        if len(errors) == 0:
            # updated RT-M is conform, we have a valid action:
            yield (name, functools.partial(make_tuple, new_od, msgs))


class RandomDecisionMaker(DecisionMaker):
    def __init__(self, seed=0, verbose=True):
        self.r = random.Random(seed)

    def __call__(self, actions):
        arr = [action for descr, action in actions]
        i = math.floor(self.r.random()*len(arr))
        return arr[i]

class InteractiveDecisionMaker(DecisionMaker):
    def __init__(self, msg="Select action:"):
        self.msg = msg

    def __call__(self, actions):
        arr = []
        for i, (key, result) in enumerate(actions):
           print(f"  {i}. {key}")
           arr.append(result)
        if len(arr) == 0:
           return

        def __choose():
           sys.stdout.write(f"{self.msg} ")
           try:
              raw = input()
              choice = int(raw) # may raise ValueError
              if choice >= 0 and choice < len(arr):
                 return arr[choice]
           except ValueError:
              pass
           print("Invalid option")
           return __choose()

        return __choose()
