import io
import os
import unittest

from transformation.schedule import rule_scheduler
from transformation.schedule.rule_scheduler import RuleSchedular
from state.devstate import DevState


class MyTestCase(unittest.TestCase):
    def setUp(self):
        state = DevState()
        self.generator = RuleSchedular(state, "", "")

    def test_empty(self):
        try:
            self.generator.generate_schedule(
                f"{os.path.dirname(__file__)}/drawio/Empty.drawio"
            )
            # buffer = io.BytesIO()
            # self.generator.generate_dot(buffer)
        except Exception as e:
            assert False

    def test_simple(self):
        try:
            self.generator.generate_schedule(
                f"{os.path.dirname(__file__)}/drawio/StartToEnd.drawio"
            )
            # buffer = io.BytesIO()
            # self.generator.generate_dot(buffer)
        except Exception as e:
            assert False

    # def test_unsupported(self):
    #     try:
    #         self.generator.generate_schedule("Tests/drawio/Unsupported.drawio")
    #         # buffer = io.BytesIO()
    #         # self.generator.generate_dot(buffer)
    #     except Exception as e:
    #         assert(False)


if __name__ == "__main__":
    unittest.main()
