from dataclasses import dataclass, asdict, astuple
from typing import TypeVar, Generic, Optional

# Some typing information for Python static type checkers
Literal = TypeVar('Literal', int, float, bool, str)  # Must be int, float, bool or str


@dataclass
class Element(Generic[Literal]):
    """
    An Element can represent one of following two things, based on the value of its attributes:

    *   An element (node or edge) in the State (id is not None). In this case the value can be None because it hasn't
        yet been read OR because the element doesn't have a value.
    *   A value for which a node has not yet been materialized in the State (id is None, value is not None).


    If you are familiar with the Modelverse Kernel, this class serves a function similar to the {id: ..., value: ...}
    dict that is used there.
    """
    id: Optional[str] = None
    value: Optional[Literal] = None

    def is_none(self) -> bool:
        return self.id is None and self.value is None


String = Element[str]
Integer = Element[int]
Float = Element[float]
Boolean = Element[bool]
