import io
import os
import uuid

from pathlib import Path

from PIL.Image import new
from jinja2 import Environment, FileSystemLoader
import json

from api.od import ODAPI
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance
from rule_executor import RuleExecutor
from state.devstate import DevState
from concrete_syntax.textual_od import parser as parser_od
from concrete_syntax.textual_cd import parser as parser_cd
from transformation.ramify import ramify
from typing import TYPE_CHECKING, Any
from helpers import get_module_path
from exceptions.conformance_exception import Conformance_Exception
from processModel import create_workflow, ProcessModel
from process import Process
import threading

class ProcessBootstrap(Process):
    def __init__(self, process_model_file: Path) -> None:
        super().__init__(process_model_file)
        bootstrap_dir = get_module_path("src/bootstrap")

        self.bootstrap_process = Process(bootstrap_dir / "bootstrap.od")
        self.bootstrap_rt_process = self.bootstrap_process.generate_runtime_object(bootstrap_dir / "bootstrap_env.py", bootstrap_dir, {"process": self})
        self._bootstrap_lock = threading.Lock()

    def step(self, rt_key, state, process_id, ports, data) -> tuple[Any, list[dict[str, str]]]:
        self.bootstrap_rt_process.reset()
        self.bootstrap_rt_process.start({("Input", "rt_state"): rt_key, ("Input", "finished_task"): process_id, ("Input", "results"): data, ("Input", "flow_output"): ports}, step_trough=False)
        self.bootstrap_rt_process.await_finished()

        self.bootstrap_process.visualise("", "x.dot")

        results = self.bootstrap_rt_process.get_results()
        self.rt_state = results[('create new runtime state', 'new_rt_state')]
        new_activities = results[('create activities data', 'data')]

        return self.rt_state, new_activities