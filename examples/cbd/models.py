# This module loads all the models (including the transformation rules) and performs a conformance-check on them.

import os
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser
from transformation.ramify import ramify

# get file contents as string
def read_file(filename):
    dir = os.path.dirname(__file__)
    with open(dir+'/'+filename) as file:
        return file.read()

def parse_and_check(state, m_cs, mm, descr: str):
    try:
        m = parser.parse_od(
            state,
            m_text=m_cs,
            mm=mm,
        )
    except Exception as e:
        e.add_note("While parsing model " + descr)
        raise
    try:
        conf = Conformance(state, m, mm)
        errors = conf.check_nominal()
        if len(errors) > 0:
            print(render_conformance_check_result(errors))
    except Exception as e:
        e.add_note("In model " + descr)
        raise
    return m

def get_metamodels(state, scd_mmm):
    mm_cs    =         read_file('models/mm_design.od')
    mm_rt_cs = mm_cs + read_file('models/mm_runtime.od')

    mm    = parse_and_check(state, mm_cs,    scd_mmm, "Design meta-model")
    mm_rt = parse_and_check(state, mm_rt_cs, scd_mmm, "Runtime meta-model")

    return (mm, mm_rt)

def get_fibonacci(state, scd_mmm):
    mm, mm_rt = get_metamodels(state, scd_mmm)

    m_cs            =        read_file('models/m_fibonacci.od')
    m_rt_initial_cs = m_cs + read_file('models/m_fibonacci_initial.od')

    m            = parse_and_check(state, m_cs,            mm,    "Fibonacci model")
    m_rt_initial = parse_and_check(state, m_rt_initial_cs, mm_rt, "Fibonacci initial state")

    return (mm, mm_rt, m, m_rt_initial)

RULE_NAMES = ["delay"]
KINDS = ["nac", "lhs", "rhs"]

def get_rules(state, rt_mm):
    rt_mm_ramified = ramify(state, rt_mm)

    rules = {} # e.g., { "delay": {"nac": <UUID>, "lhs": <UUID>, ...}, ...}

    for rule_name in RULE_NAMES:
        rule = {}
        for kind in KINDS:
            filename = f"models/r_{rule_name}_{kind}.od";
            cs = read_file(filename)
            rule_m = parse_and_check(state, cs, rt_mm_ramified, descr=f"'{filename}'")
            rule[kind] = rule_m
        rules[rule_name] = rule

    return (rt_mm_ramified, rules)