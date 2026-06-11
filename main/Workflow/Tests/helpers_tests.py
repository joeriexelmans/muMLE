from pathlib import Path

from exceptions.conformance_exception import Conformance_Exception
import re

from helpers import get_module_path
from process import Process


def model_id(val):
    if isinstance(val, str):
        return Path(val).stem
    return None


def conformance_eval(
    e: Conformance_Exception, expected_substr_err: dict[str, list[str]]
) -> bool:
    errors = e.args[0]
    nodes = expected_substr_err.keys()
    error_sort: dict[str, list[str]] = {k: [] for k in nodes}
    node_name_regex = f"'({'|'.join([f"{k}" for k in nodes])})'"
    for err in errors:
        match = re.search(node_name_regex, err)
        if not match:
            assert False, f"Unexpected conformance error found: {err}"
        error_sort[match.group(1)].append(err)

    error_amount_mismatch = [
        node
        for node, err in error_sort.items()
        if len(err) != len(expected_substr_err[node])
    ]
    assert not len(error_amount_mismatch), (
        f"Expected {len(expected_substr_err[error_amount_mismatch[0]])} errors for node '{error_amount_mismatch[0]}', found {len(error_sort[error_amount_mismatch[0]])}\n"
        f"expected regex:\n{"\n".join([f"\t-> {err}" for err in expected_substr_err[error_amount_mismatch[0]]])}\n"
        f"Found: \n{"\n".join([f"\t-> {err}" for err in error_sort[error_amount_mismatch[0]]])}\n"
    )

    for node in nodes:
        found_error_sring = f"({"|".join(error_sort[node])})"
        for expected_err in expected_substr_err[node]:
            matches = re.search(expected_err.replace(".", "[^|]"), found_error_sring)
            assert matches, (
                f"Unexpected error for node '{node}': Can not find a corresponding error for expected regex: {expected_err}\n"
                f"Found errors: \n{"\n".join([f"\t-> {err}" for err in error_sort[node]])}\n"
            )
    return True


def meta_model_test(model: str, expected_errors: dict[str, list[str]]):
    exc = None
    try:
        Process(get_module_path("models/Tests/Meta_model", model))
        assert not len(
            expected_errors
        ), f"Expected errors: \n{expected_errors}\nFound: None"
        return
    except Conformance_Exception as e:
        exc = e
    assert conformance_eval(exc, expected_errors), "Unexpected error"
