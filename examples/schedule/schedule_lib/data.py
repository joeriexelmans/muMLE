import functools
from typing import Any, Generator, Callable


class Data:
    def __init__(self, super) -> None:
        self.data: list[dict[Any, Any]] = list()
        self.success: bool = False
        self.super = super

    @staticmethod
    def store_output(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            output = func(self, *args, **kwargs)
            self.success = output
            return output
        return wrapper

    @store_output
    def store_data(self, data_gen: Generator, n: int) -> bool:
        self.data.clear()
        if n == 0:
            return True
        i: int = 0
        while (match := next(data_gen, None)) is not None:
            self.data.append(match)
            i+=1
            if i >= n:
                break
        else:
            if n == float("inf"):
                return bool(len(self.data))
            self.data.clear()
            return False
        return True

    def get_super(self) -> int:
        return self.super

    def replace(self, data: "Data") -> None:
        self.data.clear()
        self.data.extend(data.data)

    def append(self, data: Any) -> None:
        self.data.append(data)

    def clear(self) -> None:
        self.data.clear()

    def pop(self, index = -1) -> Any:
        return self.data.pop(index)

    def empty(self) -> bool:
        return len(self.data) == 0

    def __getitem__(self, index):
        return self.data[index]

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()