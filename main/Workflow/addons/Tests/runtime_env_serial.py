from env_inport import *
from rt_process import *

def choiseR():
    history.append("choiseR")
    R_value = next(gen)
    return {"flow": [["out1", "out2"][R_value]]}

def d_out():
    history.append("d_out")
    return {"flow": ["out"], "data": {"id": next(gen)}}

def d_in(id):
    history.append("d_out")
    return {"flow": ["out"], "data": {"id": id}}

def d_through(id):
    history.append("d_through")
    return {"flow": ["out"], "data": {"id": id}}

def d_print(id):
    history.append(f"d_print, id: {id}")
    return {}

def rec1():
    history.append("rec1")
    process = create_sub_process("Process_exec/RTmodelRecursive.md")
    process.start(step_trough=False)
    process.await_finished()
    return {"flow": ["out"]}

def call1():
    history.append("call1")
    process = create_sub_process("Process_exec/RTmodelFlow.md")
    process.start(step_trough=False)
    process.await_finished()
    results = process.get_results()
    history.append(results)
    return {"flow": ["out"]}

def init_check(inp):
    history.append(f"init_check: {inp}, {type(inp)}")
    return {"flow": ["out"], "data": {"out": inp}}