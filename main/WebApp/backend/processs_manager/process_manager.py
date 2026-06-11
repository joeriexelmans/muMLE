import uuid
from pathlib import Path

from typing import Dict

from process import Process
from rt_process import RT_Process
from helpers import get_module_path
from util.singleton import SingletonBase

class ProcessManager(SingletonBase):
    def __init__(self, Workflow_dir: Path):
        self.processes: Dict[str, Process] = {}
        self.runtime_objects: Dict[str, RT_Process] = {}
        self.runtime_saves: Dict[str, str] = {}
        self.dir: Path = Workflow_dir

    def create_process(self, path: str) -> str | None:
        process_id = str(uuid.uuid4())
        try:
            p = Process(path)
            self.processes[process_id] = p
            return process_id
        except Exception as e:
            print(e)
            raise e

    def init_runtime(self, process_id: str, envirement = ""):
        runtime_obj_id = str(uuid.uuid4())
        try:
            p = self.processes[process_id]

            rt = p.generate_runtime_object(
                get_module_path("addons", "runtime_env.py"),
                self.dir
            )
            self.runtime_objects[runtime_obj_id] = rt
            return runtime_obj_id
        except Exception as e:
            print(e)
            raise e


    def start(self, process_id: str, step_through: bool = True):
        rt = self.runtime_objects[process_id]
        rt.start(step_trough=step_through)

    def step(self, process_id: str):
        rt = self.runtime_objects[process_id]
        rt.step()

    def stop(self, process_id: str):
        rt = self.runtime_objects[process_id]
        rt.stop()

    def pause(self, process_id: str):
        rt = self.runtime_objects[process_id]
        rt.pause()

    def save(self, process_id: str):
        rt = self.runtime_objects[process_id]
        save_id = str(uuid.uuid4())
        self.runtime_saves[f"{process_id}{save_id}"] = rt.save()
        return save_id

    def load(self, process_id: str, state):
        rt = self.runtime_objects[process_id]
        rt.load(self.runtime_saves[f"{process_id}{state}"])

    def visualize(self, process_id: str, output_file: str):
        rt = self.runtime_objects[process_id]
        rt.Process.visualise(rt.rt_key, output_file)

    def get_runtime_info(self, process_id):
        rt = self.runtime_objects[process_id]
        return rt.get_runtime_info()
