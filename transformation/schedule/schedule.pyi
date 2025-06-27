from typing import TYPE_CHECKING
from transformation.schedule.schedule_lib import *
if TYPE_CHECKING:
    from transformation.schedule.rule_executor import RuleExecutor
    from rule_scheduler import RuleSchedular

class Schedule:
    __slots__ = {
        "start",
        "end",
        "nodes"
    }
    def __init__(self): ...

    @staticmethod
    def get_matchers(): ...
    def init_schedule(self, schedular: RuleSchedular, rule_executor: RuleExecutor, matchers): ...
    def generate_dot(self, *args, **kwargs): ...