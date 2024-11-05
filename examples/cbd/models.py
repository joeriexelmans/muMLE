import os
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser


# get file contents as string
def read_file(filename):
    dir = os.path.dirname(__file__)
    with open(dir+'/'+filename) as file:
        return file.read()

# def parse_and_check(state, cs_file, mm):
#     m_cs = read_file(cs_file)
#     try:
#         _parse_and_check(state, m_cs, mm)
#     except Exception as e:
#         e.add_note(f"While parsing '{cs_file}'")
#         raise
#     return m

def parse_and_check(state, m_cs, mm, descr: str):
    try:
        m = parser.parse_od(
            state,
            m_text=m_cs,
            mm=mm,
        )
        conf = Conformance(state, m, mm)
        errors = conf.check_nominal()
        if len(errors) > 0:
            raise Exception(render_conformance_check_result(errors))
    except Exception as e:
        e.add_note("While parsing model " + descr)
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
