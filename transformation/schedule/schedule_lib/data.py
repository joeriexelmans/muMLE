from symtable import Class
from typing import Any, Generator, Callable, Iterator, TYPE_CHECKING, override

if TYPE_CHECKING:
    from transformation.schedule.schedule_lib import DataNode


class DataState:
    def __init__(self, data: Any):
        self.data: list[dict[Any, Any]] = []

class Data:
    __slots__ = ("state", "_parent")

    def __init__(self, parent: "DataNode") -> None:
        self.state: dict[int, DataState] = dict()
        self._parent = parent

    def __dir__(self):
        return [attr for attr in super().__dir__() if attr != "_super"]

    def get_data(self, exec_id: int) -> list[dict[str, str]]:
        state = self.get_state(exec_id)
        return state.data

    def get_state(self, exec_id) -> DataState:
        return self.state[exec_id]

    def store_data(self, exec_id: int, data_gen: Generator, n: int) -> bool:
        state = self.get_state(exec_id)
        state.data.clear()
        if n == 0:
            return True
        i: int = 0
        while (match := next(data_gen, None)) is not None:
            state.data.append(match)
            i += 1
            if i >= n:
                break
        else:
            if n == float("inf"):
                return bool(len(state.data))
            state.data.clear()
            return False
        return True

    def get_parent(self) -> "DataNode":
        return self._parent

    def replace(self, exec_id: int, data: list[dict[str, str]]) -> None:
        state = self.get_state(exec_id)
        state.data.clear()
        state.data.extend(data)

    def append(self, exec_id: int, data: dict[str, str]) -> None:
        self.get_state(exec_id).data.append(data)

    def extend(self, exec_id: int, data: list[dict[str, str]]) -> None:
        self.get_state(exec_id).data.extend(data)

    def clear(self, exec_id: int) -> None:
        self.get_state(exec_id).data.clear()

    def pop(self, exec_id: int, index: int =-1) -> Any:
        return self.get_state(exec_id).data.pop(index)

    def empty(self, exec_id: int) -> bool:
        return len(self.get_state(exec_id).data) == 0

    def __getitem__(self, index):
        raise NotImplementedError

    def __iter__(self, exec_id: int) -> Iterator[dict[str, str]]:
        return self.get_state(exec_id).data.__iter__()

    def __len__(self, exec_id: int) -> int:
        return self.get_state(exec_id).data.__len__()

    def generate_stack_frame(self, exec_id: int) -> None:
        self.state[exec_id] = DataState(exec_id)

    def delete_stack_frame(self, exec_id: int) -> None:
        self.state.pop(exec_id)