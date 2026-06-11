from pathlib import Path

import pytest
from process import Process
from exceptions.conformance_exception import Conformance_Exception
from helpers_tests import meta_model_test, model_id


@pytest.mark.meta_model
@pytest.mark.parametrize(
    "model",
    [
        "single_node.md",
        "single_transition.md",
        "simple_data_flow.md",
        "simple_data_open_port.md",
    ],
    ids=model_id,
)
def test_meta_model_pass(model):
    meta_model_test(f"Pass/{model}", {})
