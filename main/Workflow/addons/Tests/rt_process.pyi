from __future__ import annotations

import threading
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Any

from process import Process


class RT_status(Enum):
    INIT = 0
    RUNNING = 1
    PAUSED = 2
    STOPPED = 3


class RT_Process:
    def start(
        self,
        init_values: dict[tuple[str, str], Any] | None = None,
        step_trough: bool = False,
    ) -> None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def stop(self) -> None: ...

    def is_finished(self) -> bool: ...

    def await_finished(
        self,
        timeout: float | None = None,
    ) -> None: ...

    def load(self, rt_save: Any) -> None: ...

    def save(self) -> Any: ...

    def step(self) -> bool: ...

    def get_results(self) -> dict[tuple[str, str], Any]: ...


def create_sub_process(file: str) -> RT_Process: ...