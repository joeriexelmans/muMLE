from time import sleep
import os

from itertools import cycle

from rt_process import *

history = list()
randomV = [1,0,1,1,0,0]
gen = cycle(randomV)

def f1():
    history.append("f1")
    return {"flow": ["out"]}

def f2():
    history.append("f2")
    return {"flow": ["out"]}

def a1():
    history.append("a1")
    return {"flow": ["out"]}

def a2():
    history.append("a2")
    return {"flow": ["out"]}

def a3():
    history.append("a3")
    return {"flow": ["out"]}

def a4():
    history.append("a4")
    return {"flow": ["out"]}

def choiseR():
    history.append("choiseR")
    R_value = next(gen)
    return {"flow": ["out1", "out2"]}

def rec1():
    history.append("rec1")
    process = create_sub_process("recursive")
    process.start(step_trough=False)
    process.await_finished()
    print("rec1")
    return {"flow": ["out"]}

def call1():
    history.append("call1")
    process = create_sub_process("funcCall")
    process.start(step_trough=True)
    process.await_finished()
    print("rec1")
    return {"flow": ["out"]}