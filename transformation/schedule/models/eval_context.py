from typing import TYPE_CHECKING, get_origin, get_args
from types import UnionType
from uuid import UUID

from jinja2 import Template

from framework.conformance import eval_context_decorator
from services.primitives.string_type import String

if TYPE_CHECKING:
    from api.od_stub_readonly import get_outgoing, get_incoming, get_slot_value, get_value, get_target, has_slot
    from eval_context_stub import *


@eval_context_decorator
def _check_all_connections(this, labels: list[list[str] | str]) -> list[str]:
    err = []
    check_incoming_exec(this, err, labels[0])
    check_outgoing_exec(this, err, labels[1])
    check_incoming_data(this, err, labels[2])
    check_outgoing_data(this, err, labels[3])
    return err

@eval_context_decorator
def _check_outgoing_exec(this, err: list[str], labels: list[str]) -> None:
    l = set(labels)
    gates = set()
    for y in get_outgoing(this, "Conn_exec"):
        if (x := get_slot_value(y, "from")) not in l:
            err.append(f"output exec gate '{x}' does not exist. Gates: {', '.join(labels)}.")
        if x in gates:
            err.append(f"output exec gate '{x}' is connected to multiple gates.")
        gates.add(x)


@eval_context_decorator
def _check_incoming_exec(this, err: list[str], labels: list[str]) -> None:
    l = set(labels)
    for y in get_incoming(this, "Conn_exec"):
        if (x := get_slot_value(y, "to")) not in l:
            err.append(f"input exec gate gate '{x}' does not exist. Gates: {', '.join(labels)}.")


@eval_context_decorator
def _check_outgoing_data(this, err: list[str], labels: list[str]) -> None:
    l = set(labels)
    for y in get_outgoing(this, "Conn_data"):
        if (x := get_slot_value(y, "from")) not in l:
            err.append(f"output data gate '{x}' does not exist. Gates: {', '.join(labels)}.")


@eval_context_decorator
def _check_incoming_data(this, err: list[str], labels: list[str]) -> None:
    l = set(labels)
    gates = set()
    for y in get_incoming(this, "Conn_data"):
        if (x := get_slot_value(y, "to")) not in l:
            err.append(f"input data gate '{x}' does not exist. Gates: {', '.join(labels)}.")
        if x in gates:
            err.append(f"input data gate '{x}' is connected to multiple gates.")
        gates.add(x)

def check_type(x: any, typ2: any) -> bool:
    origin = get_origin(typ2)
    if origin is None:
        return isinstance(x, typ2)
    args = get_args(typ2)
    if origin is UnionType:
        for tp in args:
            if check_type(x, tp):
                return True
        return False
    if not isinstance(x, origin):
        return False
    if origin in [list, set]:
        for value in x:
            if not check_type(value, args[0]):
                return False
    elif origin is tuple:
        if len(args) != len(x):
            return False
        for i, value in enumerate(x):
            if not check_type(value, args[i]):
                return False
    elif origin is dict:
        for key, value in x.items():
            if not (check_type(key, args[0]) and check_type(value, args[1])):
                return False
    return True

@eval_context_decorator
def _check_slot_code_type(this: UUID, slot: str, typ: type, unique = False, *, mandatory: bool = False, blacklist: list[str] | None = None) -> list[str]:
    err = []
    if not (has_slot(this, slot)):
        if mandatory:
            err.append(f"Missing mandatory slot: '{slot}'.")
        return err
    try:
        try:
            x = eval(get_slot_value(this, slot))
        except Exception as _:
            err.append(f"Invalid python code for {slot}: {get_slot_value(this, slot)}")
            return err

        if not check_type(x, typ):
            try:
                typ_rep = typ.__name__
            except AttributeError:
                typ_rep = str(typ)
            err.append(f"Unexpected type for {slot}: {type(x).__name__}, expected type: {typ_rep}")
            return err

        if unique and len(set(x)) != len(x):
            err.append(f"elements must be unique")
        return err
    except Exception as e:
        err.append(f"Unexpected error: {e}")
        return err


@eval_context_decorator
def _check_jinja2_code(this: UUID, slot: str) -> list[str]:
    if len(err:= check_slot_code_type(this, slot, str, mandatory=True)) != 0:
        return err
    s = eval(get_slot_value(this, slot))
    try:
        template = Template(s)
        template.render(**{"data":[{}]})
        return []
    except Exception as e:
        return [f"Invalid Jinja2 syntax for '{slot}':\n{e}\n{s}"]


@eval_context_decorator
def _check_code_syntax(code) -> list[str]:
    try:
        compile(code, "<string>", "exec")
        return []
    except SyntaxError as e:
        return [f"Invalid python code for: `{code}` :\n{e}"]

mm_eval_context = {
    "check_all_connections": _check_all_connections,
    "check_outgoing_exec": _check_outgoing_exec,
    "check_incoming_exec": _check_incoming_exec,
    "check_outgoing_data": _check_outgoing_data,
    "check_incoming_data": _check_incoming_data,
    "check_slot_code_type": _check_slot_code_type,
    "check_code_syntax": _check_code_syntax,
    "check_jinja2_code": _check_jinja2_code,
}
