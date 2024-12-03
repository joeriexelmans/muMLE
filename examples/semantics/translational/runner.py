from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.plantuml.renderer import render_object_diagram, render_class_diagram
from concrete_syntax.plantuml.make_url import make_url
from api.od import ODAPI

from transformation.ramify import ramify
from transformation.topify.topify import Topifier
from transformation.merger import merge_models

from util import loader

from examples.semantics.operational.simulator import Simulator, RandomDecisionMaker, InteractiveDecisionMaker
from examples.semantics.operational.port import models
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time
from examples.semantics.operational.port.renderer import render_port_textual, render_port_graphviz

import os
THIS_DIR = os.path.dirname(__file__)

# get file contents as string
def read_file(filename):
    with open(THIS_DIR+'/'+filename) as file:
        return file.read()

if __name__ == "__main__":
    state = DevState()
    scd_mmm = bootstrap_scd(state)

    # Load merged Petri Net and Port meta-model:
    merged_mm = loader.parse_and_check(state, read_file("merged_mm.od"), scd_mmm, "merged_mm.od")

    # Load Port initial runtime model:
    port_m_rt_initial = loader.parse_and_check(state, models.port_rt_m_cs, merged_mm, "Port-M-RT-initial")
