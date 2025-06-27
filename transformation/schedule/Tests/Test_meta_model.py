import io
import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from icecream import ic

from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from examples.schedule import rule_schedular
from examples.schedule.rule_schedular import ScheduleActionGenerator
from state.devstate import DevState
from transformation.ramify import ramify
from util import loader


class Test_Meta_Model(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = os.path.dirname(__file__)
        state = DevState()
        scd_mmm = bootstrap_scd(state)
        with open(f"{cls.dir}/models/mm_petrinet.od") as file:
            mm_s = file.read()
        with open(f"{cls.dir}/models/m_petrinet.od") as file:
            m_s = file.read()
        mm = loader.parse_and_check(state, mm_s, scd_mmm, "mm")
        m = loader.parse_and_check(state, m_s, mm, "m")
        mm_rt_ramified = ramify(state, mm)
        cls.model_param = (state, m, mm)
        cls.generator_param = (state, mm, mm_rt_ramified)

    def setUp(self):
        self.model = ODAPI(*self.model_param)
        self.out = io.StringIO()
        self.generator = ScheduleActionGenerator(
            *self.generator_param,
            directory=self.dir + "/models",
            verbose=True,
            outstream=self.out,
        )

    def _test_conformance(
        self, file: str, expected_substr_err: dict[tuple[str, str], list[list[str]]]
    ) -> None:
        try:
            self.generator.load_schedule(f"schedule/{file}")
            errors = self.out.getvalue().split("\u25b8")[1:]
            ic(errors)
            if len(errors) != len(expected_substr_err.keys()):
                ic("len total errors")
                assert len(errors) == len(expected_substr_err.keys())
            for err in errors:
                error_lines = err.strip().split("\n")
                line = error_lines[0]
                for key_pattern in expected_substr_err.keys():
                    if (key_pattern[0] in line) and (key_pattern[1] in line):
                        key = key_pattern
                        break
                else:
                    ic("no matching key")
                    ic(line)
                    assert False
                expected = expected_substr_err[key]
                if (len(error_lines) - 1) != len(expected):
                    ic("len substr errors")
                    ic(line)
                    assert (len(error_lines) - 1) == len(expected)
                it = error_lines.__iter__()
                it.__next__()
                for err_line in it:
                    if not any(
                        all(exp in err_line for exp in line_exp)
                        for line_exp in expected
                    ):
                        ic("wrong substr error")
                        ic(line)
                        ic(error_lines)
                        assert False
                expected_substr_err.pop(key)
        except AssertionError:
            raise
        except Exception as e:
            ic(e)
            assert False

    def test_no_start(self):
        self._test_conformance("no_start.od", {("Start", "Cardinality"): []})

    def test_no_end(self):
        self._test_conformance("no_end.od", {("End", "Cardinality"): []})

    def test_multiple_start(self):
        self._test_conformance("multiple_start.od", {("Start", "Cardinality"): []})

    def test_multiple_end(self):
        self._test_conformance("multiple_end.od", {("End", "Cardinality"): []})

    def test_connections_start(self):
        self._test_conformance(
            "connections_start.od",
            {
                ("Start", "start"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "out", "multiple"],
                    ["output exec", "foo_out", "exist"],
                    ["input data", "in", "exist"],
                ]
            },
        )

    def test_connections_end(self):
        self._test_conformance(
            "connections_end.od",
            {
                ("End", "end"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "foo_out", "exist"],
                    ["input data", "in", "multiple"],
                    ["input data", "out2", "exist"],
                    ["output data", "out", "exist"],
                ]
            },
        )

    def test_connections_match(self):
        self._test_conformance(
            "connections_match.od",
            {
                ("Match", "m_foo"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "foo", "exist"],
                    ["output exec", "fail", "multiple"],
                    ["input data", "foo_in", "exist"],
                    ["input data", "in", "multiple"],
                    ["output data", "foo_out", "exist"],
                ]
            },
        )

    def test_connections_rewrite(self):
        self._test_conformance(
            "connections_rewrite.od",
            {
                ("Rewrite", "r_foo1"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "foo", "exist"],
                ],
                ("Rewrite", "r_foo2"): [
                    ["output exec", "out", "multiple"],
                    ["input data", "foo_in", "exist"],
                    ["input data", "in", "multiple"],
                    ["output data", "foo_out", "exist"],
                ],
            },
        )

    def test_connections_action(self):
        self._test_conformance(
            "connections_action.od",
            {
                ("Action", "a_foo1"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "out", "multiple"],
                    ["output exec", "foo", "exist"],
                    ["input data", "in1", "multiple"],
                ],
                ("Action", "a_foo2"): [
                    ["input exec", "in", "exist"],
                    ["output exec", "out3", "multiple"],
                    ["output exec", "out", "exist"],
                    ["input data", "in", "exist"],
                    ["output data", "out", "exist"],
                ],
            },
        )

    def test_connections_modify(self):
        self._test_conformance(
            "connections_modify.od",
            {
                ("Modify", "m_foo"): [
                    ["input exec", "in", "exist"],
                    ["input exec", "in", "exist"],
                    ["output exec", "out", "exist"],
                    ["input data", "foo_in", "exist"],
                    ["output data", "foo_out", "exist"],
                    ["input data", "in", "multiple"],
                ]
            },
        )

    def test_connections_merge(self):
        self._test_conformance(
            "connections_merge.od",
            {
                ("Merge", "m_foo"): [
                    ["input exec", "in", "exist"],
                    ["input exec", "in", "exist"],
                    ["output exec", "out", "exist"],
                    ["input data", "foo_in", "exist"],
                    ["output data", "foo_out", "exist"],
                    ["input data", "in2", "multiple"],
                ]
            },
        )

    def test_connections_store(self):
        self._test_conformance(
            "connections_store.od",
            {
                ("Store", "s_foo"): [
                    ["input exec", "foo", "exist"],
                    ["output exec", "out", "multiple"],
                    ["output exec", "foo", "exist"],
                    ["input data", "foo_in", "exist"],
                    ["output data", "foo_out", "exist"],
                    ["input data", "2", "multiple"],
                ],
            },
        )

    def test_connections_schedule(self):
        self._test_conformance(
            "connections_schedule.od",
            {
                ("Schedule", "s_foo"): [
                    ["output exec", "out", "multiple"],
                    ["input data", "in2", "multiple"],
                ]
            },
        )

    def test_connections_loop(self):
        self._test_conformance(
            "connections_loop.od",
            {
                ("Loop", "l_foo"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "out", "multiple"],
                    ["output exec", "foo", "exist"],
                    ["input data", "foo_in", "exist"],
                    ["output data", "foo_out", "exist"],
                    ["input data", "in", "multiple"],
                ]
            },
        )

    def test_connections_print(self):
        self._test_conformance(
            "connections_print.od",
            {
                ("Print", "p_foo"): [
                    ["input exec", "foo_in", "exist"],
                    ["output exec", "out", "multiple"],
                    ["output exec", "foo", "exist"],
                    ["input data", "foo_in", "exist"],
                    ["output data", "out", "exist"],
                    ["input data", "in", "multiple"],
                ]
            },
        )

    def test_fields_start(self):
        self._test_conformance(
            "fields_start.od",
            {
                ("Start", "Cardinality"): [],
                ("Start", "string"): [
                    ["Unexpected type", "ports_exec_out", "str"],
                    ["Unexpected type", "ports_data_out", "str"],
                ],
                ("Start", '"int"'): [
                    ["Unexpected type", "ports_exec_out", "int"],
                    ["Unexpected type", "ports_data_out", "int"],
                ],
                ("Start", "tuple"): [
                    ["Unexpected type", "ports_exec_out", "tuple"],
                    ["Unexpected type", "ports_data_out", "tuple"],
                ],
                ("Start", "dict"): [
                    ["Unexpected type", "ports_exec_out", "dict"],
                    ["Unexpected type", "ports_data_out", "dict"],
                ],
                ("Start", "none"): [
                    ["Unexpected type", "ports_exec_out", "NoneType"],
                    ["Unexpected type", "ports_data_out", "NoneType"],
                ],
                ("Start", "invalid"): [
                    ["Invalid python", "ports_exec_out"],
                    ["Invalid python", "ports_data_out"],
                ],
                ("Start", "subtype"): [
                    ["Unexpected type", "ports_exec_out", "list"],
                    ["Unexpected type", "ports_data_out", "list"],
                ],
                ("Start", "code"): [
                    ["Unexpected type", "ports_exec_out"],
                    ["Unexpected type", "ports_data_out"],
                ],
            },
        )

    def test_fields_end(self):
        self._test_conformance(
            "fields_end.od",
            {
                ("End", "Cardinality"): [],
                ("End", "string"): [
                    ["Unexpected type", "ports_exec_in", "str"],
                    ["Unexpected type", "ports_data_in", "str"],
                ],
                ("End", '"int"'): [
                    ["Unexpected type", "ports_exec_in", "int"],
                    ["Unexpected type", "ports_data_in", "int"],
                ],
                ("End", "tuple"): [
                    ["Unexpected type", "ports_exec_in", "tuple"],
                    ["Unexpected type", "ports_data_in", "tuple"],
                ],
                ("End", "dict"): [
                    ["Unexpected type", "ports_exec_in", "dict"],
                    ["Unexpected type", "ports_data_in", "dict"],
                ],
                ("End", "none"): [
                    ["Unexpected type", "ports_exec_in", "NoneType"],
                    ["Unexpected type", "ports_data_in", "NoneType"],
                ],
                ("End", "invalid"): [
                    ["Invalid python", "ports_exec_in"],
                    ["Invalid python", "ports_data_in"],
                ],
                ("End", "subtype"): [
                    ["Unexpected type", "ports_exec_in", "list"],
                    ["Unexpected type", "ports_data_in", "list"],
                ],
                ("End", "code"): [
                    ["Unexpected type", "ports_exec_in"],
                    ["Unexpected type", "ports_data_in"],
                ],
            },
        )

    def test_fields_action(self):
        self._test_conformance(
            "fields_action.od",
            {
                ("cardinality", "Action_action"): [],
                ("Action", "string"): [
                    ["Unexpected type", "ports_exec_out", "str"],
                    ["Unexpected type", "ports_exec_in", "str"],
                    ["Unexpected type", "ports_data_out", "str"],
                    ["Unexpected type", "ports_data_in", "str"],
                ],
                ("Action", '"int"'): [
                    ["Unexpected type", "ports_exec_out", "int"],
                    ["Unexpected type", "ports_exec_in", "int"],
                    ["Unexpected type", "ports_data_out", "int"],
                    ["Unexpected type", "ports_data_in", "int"],
                ],
                ("Action", "tuple"): [
                    ["Unexpected type", "ports_exec_out", "tuple"],
                    ["Unexpected type", "ports_exec_in", "tuple"],
                    ["Unexpected type", "ports_data_out", "tuple"],
                    ["Unexpected type", "ports_data_in", "tuple"],
                ],
                ("Action", "dict"): [
                    ["Unexpected type", "ports_exec_out", "dict"],
                    ["Unexpected type", "ports_exec_in", "dict"],
                    ["Unexpected type", "ports_data_out", "dict"],
                    ["Unexpected type", "ports_data_in", "dict"],
                ],
                ("Action", "none"): [
                    ["Unexpected type", "ports_exec_out", "NoneType"],
                    ["Unexpected type", "ports_exec_in", "NoneType"],
                    ["Unexpected type", "ports_data_out", "NoneType"],
                    ["Unexpected type", "ports_data_in", "NoneType"],
                ],
                ("Action", '"invalid"'): [
                    ["Invalid python", "ports_exec_out"],
                    ["Invalid python", "ports_exec_in"],
                    ["Invalid python", "ports_data_out"],
                    ["Invalid python", "ports_data_in"],
                ],
                ("Action_action", "invalid_action"): [],
                ("Action", "subtype"): [
                    ["Unexpected type", "ports_exec_out", "list"],
                    ["Unexpected type", "ports_exec_in", "list"],
                    ["Unexpected type", "ports_data_out", "list"],
                    ["Unexpected type", "ports_data_in", "list"],
                ],
                ("Action", "code"): [
                    ["Unexpected type", "ports_exec_out"],
                    ["Unexpected type", "ports_exec_in"],
                    ["Unexpected type", "ports_data_out"],
                    ["Unexpected type", "ports_data_in"],
                ],
            },
        )

    def test_fields_modify(self):
        self._test_conformance(
            "fields_modify.od",
            {
                ("Modify", "string"): [
                    ["Unexpected type", "rename", "str"],
                    ["Unexpected type", "delete", "str"],
                ],
                ("Modify", "list"): [["Unexpected type", "rename", "list"]],
                ("Modify", "set"): [["Unexpected type", "rename", "set"]],
                ("Modify", "tuple"): [
                    ["Unexpected type", "rename", "tuple"],
                    ["Unexpected type", "delete", "tuple"],
                ],
                ("Modify", "dict"): [["Unexpected type", "delete", "dict"]],
                ("Modify", "none"): [
                    ["Unexpected type", "rename", "NoneType"],
                    ["Unexpected type", "delete", "NoneType"],
                ],
                ("Modify", "invalid"): [
                    ["Invalid python", "rename"],
                    ["Invalid python", "delete"],
                ],
                ("Modify", "subtype"): [
                    ["Unexpected type", "rename", "dict"],
                    ["Unexpected type", "delete", "list"],
                ],
                ("Modify", "code"): [
                    ["Unexpected type", "rename"],
                    ["Unexpected type", "delete"],
                ],
                ("Modify", "joined"): [["rename", "delete", "disjoint"]],
            },
        )

    def test_fields_merge(self):
        self._test_conformance(
            "fields_merge.od",
            {
                ("cardinality", "Merge_ports_data_in"): [],
                ("Merge", "string"): [["Unexpected type", "ports_data_in", "str"]],
                ("Merge", "tuple"): [["Unexpected type", "ports_data_in", "tuple"]],
                ("Merge", "dict"): [["Unexpected type", "ports_data_in", "dict"]],
                ("Merge", "none"): [["Unexpected type", "ports_data_in", "NoneType"]],
                ("Merge", "invalid"): [["Invalid python", "ports_data_in"]],
                ("Merge", "subtype"): [["Unexpected type", "ports_data_in", "list"]],
                ("Merge", "code"): [["Unexpected type", "ports_data_in"]],
                ("Merge", "no"): [["Missing", "slot", "ports_data_in"]],
            },
        )

    def test_fields_store(self):
        self._test_conformance(
            "fields_store.od",
            {
                ("cardinality", "Store_ports"): [],
                ("Store", "string"): [["Unexpected type", "ports", "str"]],
                ("Store", "tuple"): [["Unexpected type", "ports", "tuple"]],
                ("Store", "dict"): [["Unexpected type", "ports", "dict"]],
                ("Store", "none"): [["Unexpected type", "ports", "NoneType"]],
                ("Store", "invalid"): [["Invalid python", "ports"]],
                ("Store", "subtype"): [["Unexpected type", "ports", "list"]],
                ("Store", "code"): [["Unexpected type", "ports"]],
                ("Store", "no"): [["Missing", "slot", "ports"]],
            },
        )
        
    def test_fields_print(self):
        self._test_conformance(
            "fields_print.od",
            {
                ("Print_custom", "list_custom"): [["Unexpected type", "custom", "list"]],
                ("Print_custom", "set_custom"): [["Unexpected type", "custom", "set"]],
                ("Print_custom", "tuple_custom"): [["Unexpected type", "custom", "tuple"]],
                ("Print_custom", "dict_custom"): [["Unexpected type", "custom", "dict"]],
                ("Print_custom", "none_custom"): [["Unexpected type", "custom", "NoneType"]],
                ("Print_custom", "invalid_custom"): [["Invalid python", "custom"]],
                ("Print_custom", "subtype_custom"): [["Unexpected type", "custom", "list"]],
                ("Print_custom", "code_custom"): [["Unexpected type", "custom"]],
            },
        )


if __name__ == "__main__":
    unittest.main()
