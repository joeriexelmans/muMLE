from icecream import ic

from concrete_syntax.textual_od.renderer import render_od
from transformation.schedule.Tests import Test_xmlparser
from util import loader
from transformation.ramify import ramify
from examples.petrinet.renderer import show_petri_net

from transformation.schedule.rule_scheduler import *

if __name__ == "__main__":
    import os
    THIS_DIR = os.path.dirname(__file__)

    # get file contents as string
    def read_file(filename):
        with open(THIS_DIR+'/'+filename) as file:
            return file.read()


    state = DevState()
    scd_mmm = bootstrap_scd(state)

    # Read models from their files
    mm_cs           =         read_file('metamodels/mm_design.od')
    mm_rt_cs        = mm_cs + read_file('metamodels/mm_runtime.od')
    # m_cs            =         read_file('models/m_example_simple.od')
    # m_rt_initial_cs = m_cs +  read_file('models/m_example_simple_rt_initial.od')
    # m_cs            =         read_file('models/m_example_mutex.od')
    # m_rt_initial_cs = m_cs +  read_file('models/m_example_mutex_rt_initial.od')
    m_cs            =         read_file('models/m_example_simple.od')
    m_rt_initial_cs = m_cs +  read_file('models/m_example_simple_rt_initial.od')

    # Parse them
    mm           = loader.parse_and_check(state, mm_cs,           scd_mmm, "Petri-Net Design meta-model")
    mm_rt        = loader.parse_and_check(state, mm_rt_cs,        scd_mmm, "Petri-Net Runtime meta-model")
    m            = loader.parse_and_check(state, m_cs,            mm,      "Example model")
    m_rt_initial = loader.parse_and_check(state, m_rt_initial_cs, mm_rt,   "Example model initial state")
    mm_rt_ramified = ramify(state, mm_rt)




    action_generator = RuleSchedular(state, mm_rt, mm_rt_ramified, verbose=True, directory="models")

    # if action_generator.load_schedule(f"petrinet.od"):
    # if action_generator.load_schedule("schedules/combinatory.drawio"):
    if action_generator.load_schedule("schedules/petrinet3.drawio"):


        action_generator.generate_dot("../dot.dot")
        code, message = action_generator.run(ODAPI(state, m_rt_initial, mm_rt))
        print(f"{code}: {message}")
