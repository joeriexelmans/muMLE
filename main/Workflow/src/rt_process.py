import threading
from typing import Any

import uuid
from concurrent.futures import thread
from pathlib import Path
from queue import Queue
from time import sleep

import icecream

from helpers import load_module_from_file
from process import Process
from enum import Enum

class RT_status(Enum):
    INIT = 0
    RUNNING = 1
    PAUSED = 2
    STOPPED = 3

class RT_Process:
    def __init__(self, process, env_file: Path, process_dir: Path, parameters: dict[str, Any]):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

        self.Process: Process = process
        self.ProcessLoaded: dict[str, Process] = {env_file.resolve().__str__(): process}
        self.env = load_module_from_file(env_file, {**parameters, "create_sub_process": self.create_sub_process})

        self.rt_key = self.Process.rt_init[0]
        self.status: RT_status = RT_status.INIT
        self.results = Queue()
        self.threads: dict[str, thread] = {}
        self.process_dir: Path = process_dir

    def start(self, init_values:dict[(str, str), Any] | None =None, step_trough:bool = False):
        if init_values is None:
            init_values = dict()

        assert self.status == RT_status.INIT
        self.rt_key, running_places = self.Process.start(self.rt_key, init_values)
        self.status = RT_status.RUNNING
        for place in running_places:
            self.__run_process(place["Place"], place["Process"], place["Id"], kwargs=place["Data"])

        if step_trough:
            return
        self.__start_listener()


    def pause(self):
        assert self.status == RT_status.RUNNING
        self.status = RT_status.PAUSED
        self.results.put(None)  # unblock listener

    def resume(self):
        assert self.status == RT_status.PAUSED
        self.__start_listener()

    def reset(self):
        self.status = RT_status.INIT
        self.rt_key = self.Process.rt_init[0]

    def __start_listener(self):
        self.status = RT_status.RUNNING
        threading.Thread(
            target=self._result_listener,
            daemon=True,
        ).start()

    def stop(self):
        assert self.status != RT_status.STOPPED

        with self._cond:
            self.status = RT_status.STOPPED
            self.results.put(None)  # unblock listener
            self._cond.notify_all()

        with self._lock:
            for t in self.threads.values():
                t.join()

    def is_finished(self):
        return self.status == RT_status.STOPPED

    def await_finished(self, timeout: float | None = None):
        with self._cond:
            self._cond.wait_for(
                lambda: self.status == RT_status.STOPPED,
                timeout=timeout
            )


    def load(self, rt_save):
        self.stop()
        self.rt_key = rt_save
        if not self.results.empty():
            self.results = Queue()
        self.status = RT_status.INIT

    def save(self):
        return self.rt_key



    def __run_process(self, place_name, process_name, process_id, kwargs):
        try:
            method = getattr(self.env, process_name)
        except AttributeError:
            pass

        def _run():
            try:
                result = method(**kwargs)
                self.results.put({
                    "process_id": process_id,
                    "process": process_name,
                    "place": place_name,
                    "status": "done",
                    "output": result,
                    "kwargs": kwargs
                })
            except Exception as e:
                self.results.put({
                    "process_id": process_id,
                    "process": process_name,
                    "place": place_name,
                    "status": "error",
                    "output": {"flow": ["error"]},
                    "error": str(e),
                    "kwargs": kwargs
                })
        with self._lock:
            if self.status != RT_status.STOPPED:
                thread = threading.Thread(
                    target=_run,
                    daemon=True,
                )
                self.threads[process_id] = thread
                thread.start()

    def step(self):
        result = self.results.get()
        if result is None:
            return False
        self.threads.pop(result["process_id"])
        self._on_result(result)
        return True


    def _result_listener(self):
        b = True
        while (self.status == RT_status.RUNNING) and b:
            b = self.step()

    def _on_result(self, result: dict):
        """
        Triggered immediately when a task finishes.
        """
        output = result.get("output", {"data": {}, "flow": []})
        self.rt_key, next_states = self.Process.step(self.rt_key, result.get("place"), result.get("process_id"), output.get("flow", []), output.get("data", {}))
        if len(next_states):
            for next_state in next_states:
                self.__run_process(next_state["Place"], next_state["Process"], next_state["Id"], kwargs=next_state["Data"])
        else:
            if self.Process.is_finished(self.rt_key):
                with self._cond:
                    self.status = RT_status.STOPPED
                    self._cond.notify_all()

    def get_runtime_info(self):
        return self.Process.get_runtime_info(self.rt_key)


    def create_sub_process(self, file: str):
        # init by copying
        new = RT_Process.__new__(RT_Process)
        new.__dict__ = self.__dict__.copy()
        print(self.process_dir / file)
        # reinit independent vars
        new._lock = threading.Lock()
        new._cond = threading.Condition(new._lock)
        new.results = Queue()
        new.threads = {}

        file = (self.process_dir / file).resolve()
        process = self.ProcessLoaded.get(file.__str__())
        if process is None:
            process = Process(file)
            self.ProcessLoaded[file.__str__()] = process

        new.Process = process

        new.rt_key = new.Process.rt_init[0]
        new.status = RT_status.INIT
        new.results = Queue()
        return new

    def get_results(self) -> dict[tuple[str, str], Any]:
        return self.Process.get_data_state(self.rt_key)