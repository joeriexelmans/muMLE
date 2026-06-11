from itertools import cycle
from time import sleep

history = []
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

def choiseR():
    history.append("choiseR")
    R_value = next(gen)
    return {"flow": ["out1", "out2"][R_value]}