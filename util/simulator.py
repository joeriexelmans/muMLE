import abc
import random
import math
import functools
import sys
from typing import Callable, Generator

from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.common import indent
from concrete_syntax.textual_od.renderer import render_od
from transformation.cloner import clone_od
from api.od import ODAPI


class DecisionMaker:
    @abc.abstractmethod
    def __call__(self, actions):
        pass

class RandomDecisionMaker(DecisionMaker):
    def __init__(self, seed=0, verbose=True):
        self.seed = seed
        self.r = random.Random(seed)

    def __str__(self):
        return f"RandomDecisionMaker(seed={self.seed})"

    def __call__(self, actions):
        arr = [action for descr, action in actions]
        i = math.floor(self.r.random()*len(arr))
        return arr[i]

class InteractiveDecisionMaker(DecisionMaker):
    # auto_proceed: whether to prompt if there is only one enabled action
    def __init__(self, msg="Select action:", auto_proceed=False):
        self.msg = msg
        self.auto_proceed = auto_proceed

    def __str__(self):
        return f"InteractiveDecisionMaker()"

    def __call__(self, actions):
        arr = []
        for i, (key, result) in enumerate(actions):
           print(f"  {chr(97+i)}. {key}")
           arr.append(result)
        if len(arr) == 0:
           return
        if len(arr) == 1 and self.auto_proceed:
            return arr[0]

        def __choose():
           sys.stdout.write(f"{self.msg} ")
           try:
              raw = input()
              choice = int(ord(raw)-97) # may raise ValueError
              if choice >= 0 and choice < len(arr):
                 return arr[choice]
           except ValueError:
              pass
           print("Invalid option")
           return __choose()

        return __choose()



class MinimalSimulator:
    def __init__(self,
        action_generator: Callable[[any], Generator[any, None, None]],
        decision_maker: DecisionMaker = RandomDecisionMaker(seed=0),

        # Returns 'None' to keep running, or a string to end simulation
        # Can also have side effects, such as rendering the model, and performing a conformance check.
        # BTW, Simulation will always end when there are no more enabled actions.
        termination_condition=lambda model: None,

        verbose=True,
    ):
        self.action_generator = action_generator
        self.decision_maker = decision_maker
        self.termination_condition = termination_condition
        self.verbose = verbose

    def _print(self, *args):
        if self.verbose:
            print(*args)

    # Run simulation until termination condition satisfied
    def run(self, model):
        self._print("Start simulation")
        self._print(f"Decision maker: {self.decision_maker}")
        step_counter = 0
        while True:
            termination_reason = self.termination_condition(model)
            if termination_reason != None:
                self._print(f"Termination condition satisfied.\nReason: {termination_reason}.")
                break

            chosen_action = self.decision_maker(self.action_generator(model))

            if chosen_action == None:
                self._print(f"No enabled actions.")
                break

            (model, msgs) = chosen_action()
            self._print(indent('\n'.join(f"▸ {msg}" for msg in msgs), 4))

            step_counter += 1

        self._print(f"Executed {step_counter} steps.")
        return model
