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
              "rules/all_incoming.od",
              "rules/reduce_incoming.od",
        ]

    def init_schedule(self, scheduler, rule_executer, matchers):
        sub_start_1 = Start(['out', 'foo'], ['t', 'foo'])
        sub_end_2 = End(['rrrreee', 'in'], [])
        self.start = sub_start_1
        self.end = sub_end_2
        reduceplace_5 = Rewrite("rules/reduce_incoming.od")
        iterateplaces_3 = Loop()
        incomingplaces_4 = Match("rules/all_incoming.od", 1)

        sub_start_1.connect(incomingplaces_4,"out","in")
        incomingplaces_4.connect(iterateplaces_3,"fail","in")
        incomingplaces_4.connect(iterateplaces_3,"success","in")
        iterateplaces_3.connect(sub_end_2,"out","in")
        iterateplaces_3.connect(reduceplace_5,"it","in")
        reduceplace_5.connect(iterateplaces_3,"out","in")
        sub_start_1.connect_data(incomingplaces_4, "t", "in", False)
        incomingplaces_4.connect_data(iterateplaces_3, "out", "in", True)
        iterateplaces_3.connect_data(reduceplace_5, "out", "in", False)

        reduceplace_5.init_rule(matchers["rules/reduce_incoming.od"], rule_executer)
        incomingplaces_4.init_rule(matchers["rules/all_incoming.od"], rule_executer)

        self.nodes = [
            reduceplace_5,
            sub_start_1,
            iterateplaces_3,
            incomingplaces_4,
            sub_end_2,
        ]
        return None

    def generate_dot(self, *args, **kwargs):
        return self.start.generate_dot(*args, **kwargs)
