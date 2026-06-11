from pathlib import Path
from time import sleep, time
from typing import Any

import pytest

from helpers import get_module_path
from process import Process
from rt_process import RT_Process


def wait_until(predicate, msg, timeout=1.0, interval=0.001):
    start = time()
    while time() - start < timeout:
        if predicate():
            return
        sleep(interval)
    raise AssertionError(msg)


@pytest.mark.process
@pytest.mark.parametrize(
    "model, env, steps, history_trace",
    [
        # pytest.param(
        #     "RTmodelChoise.md",
        #     "runtime_env_serial.py",
        #     20,
        #     [
        #         "a1",
        #         "choiseR",
        #         "a3",
        #         "a1",
        #         "choiseR",
        #         "a2",
        #         "a1",
        #         "choiseR",
        #         "a3",
        #         "a1",
        #         "choiseR",
        #         "a3",
        #         "a1",
        #         "choiseR",
        #         "a2",
        #         "a1",
        #         "choiseR",
        #         "a2",
        #         "a1",
        #         "choiseR",
        #     ],
        #     id="Exec_choise_serial",
        # ),
        pytest.param(
            "RTmodelData.md",
            "runtime_env_serial.py",
            3,
            ["d_out", "d_through", "d_print, id: 1"],
            id="Exec_data_transfer",
        ),
    ],
)
def test_process_exec_serial(model: str, env: str, steps, history_trace) -> None:
    p = Process(get_module_path("models/Tests/Process_exec", model))
    RT_obj: RT_Process = p.generate_runtime_object(get_module_path("addons/Tests", env),
                                                   get_module_path("models/Tests", ""))
    assert (
        len(RT_obj.env.history) == 0
    ), "Wrong starting value to test executed functions"
    RT_obj.start(step_trough=True)
    for i in range(steps - 1):
        RT_obj.step()
        wait_until(
            lambda: len(RT_obj.env.history) == i + 2,
            "Incorrect amount of execution steps taken",
        )
    assert RT_obj.env.history == history_trace, "Incorrect trace executed"


@pytest.mark.process
@pytest.mark.parametrize(
    "model, env, steps_actions",
    [
        pytest.param(
            "RTmodelChoise.md",
            "runtime_env_multi.py",
            [(1,2), (2,4), (6,8), (7, 10)],
            id="Exec_choise_multi",
        ),
        pytest.param(
            "RTmodelSync.md",
            "runtime_env_multi.py",
            [(0,1),(1,3),(2,3),(3,4),(4,5)],
            id="Exec_choise_sync",
        ),
    ],
)
def test_process_exec_mult(model: str, env: str, steps_actions) -> None:
    p = Process(get_module_path("models/Tests/Process_exec", model))
    RT_obj: RT_Process = p.generate_runtime_object(get_module_path("addons/Tests", env),
                                                   get_module_path("models/Tests", ""))
    assert (
        len(RT_obj.env.history) == 0
    ), "Wrong starting value to test executed functions"
    RT_obj.start(step_trough=True)
    prev_steps = 0
    for steps, total_actions in steps_actions:
        for _ in range(prev_steps, steps):
            RT_obj.step()
        prev_steps = steps
        wait_until(
            lambda: len(RT_obj.env.history) == total_actions,
            "Incorrect amount of execution steps taken",
        )

@pytest.mark.env
@pytest.mark.parametrize(
    "model, env, trace",
    [
        pytest.param(
            "RTmodelRecursive.md",
            "runtime_env_serial.py",
            ['choiseR', 'rec1', 'choiseR', 'a1'],
            id="Exec_env",
        ),
        pytest.param(
            "RTmodelCall.md",
            "runtime_env_serial.py",
            ['a1', 'call1', 'a1', 'a2', 'a3', {('activity 3', 'new_port_1'): None}, 'a3'],
            id="Exec_env",
        ),
    ])
def test_process_exec_env(model: str, env: str, trace: str) -> None:
    p = Process(get_module_path("models/Tests/Process_exec", model))
    RT_obj: RT_Process = p.generate_runtime_object(get_module_path("addons/Tests", env),
                                                   get_module_path("models/Tests", ""))
    RT_obj.start()
    RT_obj.await_finished()
    assert RT_obj.env.history == trace, "Incorrect trace executed"

@pytest.mark.env
@pytest.mark.parametrize(
    "model, env, init, result, trace",
    [
        pytest.param(
            "RTmodelInitCheck.md",
            "runtime_env_serial.py",
            {("init", "out"): 69420},
            {("init", "out"): 69420},
            ["init_check: 69420, <class 'int'>"],
            id="Exec_data_init_int",
        ),
        pytest.param(
            "RTmodelInitCheck.md",
            "runtime_env_serial.py",
            {("init", "out"): "69420"},
            {("init", "out"): "69420"},
            ["init_check: 69420, <class 'str'>"],
            id="Exec_data_init_str_int",
        ),
        pytest.param(
            "RTmodelInitCheck.md",
            "runtime_env_serial.py",
            {("init", "out"): {"some_json_content": ["some_values123", 456]}},
            {("init", "out"): {"some_json_content": ["some_values123", 456]}},
            ["init_check: {'some_json_content': ['some_values123', 456]}, <class 'dict'>"],
            id="Exec_data_init_json",
        ),
    ])
def test_process_data_init(model: str, env: str, init: dict[tuple[str, str], Any], result: dict[tuple[str, str], Any], trace: str) -> None:
    p = Process(get_module_path("models/Tests/Process_exec", model))
    RT_obj: RT_Process = p.generate_runtime_object(get_module_path("addons/Tests", env),
                                                   get_module_path("models/Tests", ""))
    RT_obj.start(init, step_trough=True)
    RT_obj.step()
    RT_obj.await_finished()
    r = RT_obj.get_results()
    assert RT_obj.env.history == trace, "Incorrect trace executed"
    assert r == result, "Incorrect return value"