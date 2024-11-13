from util import loader

import os
THIS_DIR = os.path.dirname(__file__)

# get file contents as string
def read_file(filename):
    with open(THIS_DIR+'/'+filename) as file:
        return file.read()

def load_metamodels(state, scd_mmm):
    mm_cs    =         read_file('models/mm_design.od')
    mm_rt_cs = mm_cs + read_file('models/mm_runtime.od')

    mm    = loader.parse_and_check(state, mm_cs,    scd_mmm, "Design meta-model")
    mm_rt = loader.parse_and_check(state, mm_rt_cs, scd_mmm, "Runtime meta-model")

    return (mm, mm_rt)

def load_fibonacci(state, scd_mmm):
    mm, mm_rt = load_metamodels(state, scd_mmm)

    m_cs            =        read_file('models/m_fibonacci.od')
    m_rt_initial_cs = m_cs + read_file('models/m_fibonacci_initial.od')

    m            = loader.parse_and_check(state, m_cs,            mm,    "Fibonacci model")
    m_rt_initial = loader.parse_and_check(state, m_rt_initial_cs, mm_rt, "Fibonacci initial state")

    return (mm, mm_rt, m, m_rt_initial)


RULES0 = ["delay_in", "delay_out", "function_out"] # high priority
RULES1 = ["advance_time"] # low priority

def load_rules(state, mm_rt_ramified):
    get_filename = lambda rule_name, kind: f"{THIS_DIR}/models/r_{rule_name}_{kind}.od"

    rules0 = loader.load_rules(state, get_filename, mm_rt_ramified, RULES0)
    rules1  = loader.load_rules(state, get_filename, mm_rt_ramified, RULES1)

    return rules0, rules1
