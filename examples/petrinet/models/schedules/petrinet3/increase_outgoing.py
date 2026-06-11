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
              "rules/increase_outgoing.od",
              "rules/all_outgoing.od",
        ]

    def init_schedule(self, scheduler, rule_executer, matchers):
        sub_end_2 = End(['rrrreee', 'in'], [])
        sub_start_1 = Start(['out', 'foo'], ['t', 'foo'])
        self.start = sub_start_1
        self.end = sub_end_2
        increaseplace_4 = Rewrite("rules/increase_outgoing.od")
        iterateplaces_3 = Loop()
        outgoingplaces_5 = Match("rules/all_outgoing.od", 1)

        sub_start_1.connect(outgoingplaces_5,"out","in")
        outgoingplaces_5.connect(iterateplaces_3,"fail","in")
        outgoingplaces_5.connect(iterateplaces_3,"success","in")
        iterateplaces_3.connect(increaseplace_4,"it","in")
        iterateplaces_3.connect(sub_end_2,"out","in")
        increaseplace_4.connect(iterateplaces_3,"out","in")
        sub_start_1.connect_data(outgoingplaces_5, "t", "in", False)
        outgoingplaces_5.connect_data(iterateplaces_3, "out", "in", True)
        iterateplaces_3.connect_data(increaseplace_4, "out", "in", False)

        increaseplace_4.init_rule(matchers["rules/increase_outgoing.od"], rule_executer)
        outgoingplaces_5.init_rule(matchers["rules/all_outgoing.od"], rule_executer)

        self.nodes = [
            increaseplace_4,
            sub_end_2,
            sub_start_1,
            iterateplaces_3,
            outgoingplaces_5,
        ]
        return None

    def generate_dot(self, *args, **kwargs):
        return self.start.generate_dot(*args, **kwargs)
