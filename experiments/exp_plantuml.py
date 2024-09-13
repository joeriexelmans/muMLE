from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.ramify import ramify
from transformation import rewriter
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from pattern_matching import mvs_adapter
from pattern_matching.matcher import MatcherVF2
from renderer import plantuml

def main():
    state = DevState()
    root = state.read_root() # id: 0

    scd_mm_id = bootstrap_scd(state)

    uml = ""

    # Render SCD Meta-Model as Object Diagram
    uml += plantuml.render_package("Object Diagram", plantuml.render_object_diagram(state, scd_mm_id, scd_mm_id, prefix_ids="od_"))

    # Render SCD Meta-Model as Class Diagram
    uml += plantuml.render_package("Class Diagram", plantuml.render_class_diagram(state, scd_mm_id, prefix_ids="cd_"))

    # Render conformance
    uml += plantuml.render_trace_conformance(state, scd_mm_id, scd_mm_id, prefix_inst_ids="od_", prefix_type_ids="cd_")

    print(uml)


if __name__ == "__main__":
    main()