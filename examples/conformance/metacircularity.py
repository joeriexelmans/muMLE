from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from services.scd import SCD
from concrete_syntax.plantuml import renderer as plantuml

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