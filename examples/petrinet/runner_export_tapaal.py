from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from util import loader

from examples.petrinet.translational_semantics.tapaal.exporter import export_tapaal

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
    m_cs            =         read_file('models/m_example_mutex.od')
    m_rt_initial_cs = m_cs +  read_file('models/m_example_mutex_rt_initial.od')
    # m_cs            =         read_file('models/m_example_inharc.od')
    # m_rt_initial_cs = m_cs +  read_file('models/m_example_inharc_rt_initial.od')

    # Parse them
    mm           = loader.parse_and_check(state, mm_cs,           scd_mmm, "Petri-Net Design meta-model")
    mm_rt        = loader.parse_and_check(state, mm_rt_cs,        scd_mmm, "Petri-Net Runtime meta-model")
    m            = loader.parse_and_check(state, m_cs,            mm,      "Example model")
    m_rt_initial = loader.parse_and_check(state, m_rt_initial_cs, mm_rt,   "Example model initial state")

    with open('exported.tapn', 'w') as f:
        f.write(export_tapaal(state, m=m_rt_initial, mm=mm_rt))
