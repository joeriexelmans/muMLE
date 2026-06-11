#generated from somewhere i do not now but it here so live with it

from transformation.schedule.schedule_lib import *

class Schedule:
    def __init__(self):
        self.start: Start | None = None
        self.end: End | None = None
        self.nodes: list[DataNode] = []

    @staticmethod
    def get_matchers():
        return [
              "rules/transition.od",
        ]

    def init_schedule(self, scheduler, rule_executer, matchers):
        end_6 = End(['in'], [])
        start_1 = Start(['out'], [])
        self.start = start_1
        self.end = end_6
        increaseoutgoing_5 = SubSchedule(scheduler, "schedules/petrinet3/increase_outgoing.od")
        reduceincoming_4 = SubSchedule(scheduler, "schedules/petrinet3/reduce_incoming.od")
        findfirstthatcanfire_3 = SubSchedule(scheduler, "schedules/petrinet3/check_nac.od")
        alltranstions_2 = Match("rules/transition.od", float("inf"))

        start_1.connect(alltranstions_2,"out","in")
        alltranstions_2.connect(end_6,"fail","in")
        alltranstions_2.connect(findfirstthatcanfire_3,"success","out")
        findfirstthatcanfire_3.connect(reduceincoming_4,"in","out")
        reduceincoming_4.connect(increaseoutgoing_5,"in","out")
        increaseoutgoing_5.connect(end_6,"in","in")
        alltranstions_2.connect_data(findfirstthatcanfire_3, "out", "t", False)
        findfirstthatcanfire_3.connect_data(reduceincoming_4, "t", "t", False)
        findfirstthatcanfire_3.connect_data(increaseoutgoing_5, "t", "t", False)

        alltranstions_2.init_rule(matchers["rules/transition.od"], rule_executer)

        self.nodes = [
            end_6,
            increaseoutgoing_5,
            start_1,
            reduceincoming_4,
            findfirstthatcanfire_3,
            alltranstions_2,
        ]
        return None

    def generate_dot(self, *args, **kwargs):
        return self.start.generate_dot(*args, **kwargs)
