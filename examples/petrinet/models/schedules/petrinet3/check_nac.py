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
              "rules/input_without_token.od",
        ]

    def init_schedule(self, scheduler, rule_executer, matchers):
        sub_end_2 = End(['rrrreee', 'in'], ['t'])
        sub_start_1 = Start(['out', 'foo'], ['t', 'foo'])
        self.start = sub_start_1
        self.end = sub_end_2
        checknac_4 = Match("rules/input_without_token.od", 1)
        iteratetransitions_3 = Loop()

        sub_start_1.connect(iteratetransitions_3,"out","in")
        iteratetransitions_3.connect(checknac_4,"it","in")
        checknac_4.connect(iteratetransitions_3,"success","in")
        checknac_4.connect(sub_end_2,"fail","in")
        sub_start_1.connect_data(iteratetransitions_3, "t", "in", True)
        iteratetransitions_3.connect_data(checknac_4, "out", "in", False)
        iteratetransitions_3.connect_data(sub_end_2, "out", "t", False)

        checknac_4.init_rule(matchers["rules/input_without_token.od"], rule_executer)

        self.nodes = [
            sub_end_2,
            checknac_4,
            iteratetransitions_3,
            sub_start_1,
        ]
        return None

    def generate_dot(self, *args, **kwargs):
        return self.start.generate_dot(*args, **kwargs)
