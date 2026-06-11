from pathlib import Path

import pytest
from process import Process
from exceptions.conformance_exception import Conformance_Exception
from helpers_tests import meta_model_test, model_id


@pytest.mark.meta_model
@pytest.mark.parametrize(
    "model, expected_errors",
    [
        pytest.param(
            "missing_process.md",
            {"a1": ["cardinality.*Place_Process.*bounds"]},
            id="missing_process",
        ),
        pytest.param(
            "missing_RTState.md",
            {"RTState": ["Cardinality.*multiplicity.*0"]},
            id="missing_RTState",
        ),
        pytest.param(
            "unlinked_port.md",
            {"a2flow_in1": ["constraint.*Port.*connected.*input.*output"]},
            id="unlinked_port",
        ),
        pytest.param(
            "double_linked_port.md",
            {
                "a2flow_in1": [
                    "cardinality.*Port_flow_in.*bounds",
                    "Local.*constraint.*Port.*connected.*input.*output",
                ],
            },
            id="double_linked_port",
        ),
        pytest.param(
            "simple_data_flow_missing_port_data.md",
            {
                "a1": ["Port.*does not have a Port_data connected"],
            },
            id="missing_port_data",
        ),
        pytest.param(
            "simple_data_flow_missing_RT_data_connect.md",
            {"d1data_out1": ["cardinality.*RT_data_connect.*bounds"]},
            id="missing_RT_data_connection",
        ),
    ],
)
def test_meta_model_failures(model: str, expected_errors: dict[str, list[str]]):
    meta_model_test(f"Fail/{model}", expected_errors)
