from typing import TYPE_CHECKING
from transformation.schedule.schedule_lib import *
if TYPE_CHECKING:
    from transformation.schedule.rule_executor import RuleExecutor
    from rule_scheduler import RuleScheduler

class Schedule:
    __slots__ = {
        "start",
        "end",
        "nodes"
    }
    def __init__(self): ...

    @staticmethod
    def get_matchers(): ...
    def init_schedule(self, scheduler: RuleScheduler, rule_executor: RuleExecutor, matchers): ...
    def generate_dot(self, *args, **kwargs): ...