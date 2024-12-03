# Model transformation experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.matcher import match_od
from transformation.ramify import ramify
from transformation.cloner import clone_od
from transformation import rewriter
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as make_plantuml_url
from concrete_syntax.textual_od import parser, renderer
from util.timer import Timer

if __name__ == "__main__":
    state = DevState()
    root = state.read_root() # id: 0

    # Meta-meta-model: a class diagram that describes the language of class diagrams
    scd_mmm_id = bootstrap_scd(state)
    int_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "Integer")))
    string_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "String")))

    dsl_mm_cs = """
        Rare:Class
        Many:Class
        ManyB:Class
        Other:Class
        OtherB:Class
        OtherC:Class
        ass:Association(Many->ManyB)
    """
    dsl_mm_id = parser.parse_od(state, dsl_mm_cs, mm=scd_mmm_id)
    
    dsl_m_cs = """
        rare:Rare
        many0:Many
        many1:Many
        many2:Many
        many3:Many
        many4:Many
        many5:ManyB
        many6:ManyB
        many7:ManyB
        many8:ManyB

        :ass (many2->many6)
        :ass (many3->many8)

        # other0:Other
        # other1:OtherC
        # other2:Other
        # other3:Other
        # other4:Other
        # other5:OtherB
        # other6:OtherB
        # other7:OtherB
        # other8:OtherB
        # other9:OtherB
        # other10:OtherB
        # other11:OtherC
        # other12:OtherC
        # other13:OtherC
        # other14:OtherC

        # other1099:OtherB
        # other1199:OtherC
        # other1299:OtherC
        # other1399:OtherC
        # other1499:OtherC
    """
    dsl_m_id = parser.parse_od(state, dsl_m_cs, mm=dsl_mm_id)

    # RAMify MM
    prefix = "RAM_" # all ramified types can be prefixed to distinguish them a bit more
    ramified_mm_id = ramify(state, dsl_mm_id, prefix)
    ramified_int_mm_id = ramify(state, int_mm_id, prefix)

    # LHS - pattern to match

    # TODO: enable more powerful constraints
    pattern_cs = f"""
        # object to match
        rare:{prefix}Rare {{
        }}

        many:{prefix}Many
        manyB:{prefix}ManyB
        manyB2:{prefix}ManyB
    """
    pattern_id = parser.parse_od(state, pattern_cs, mm=ramified_mm_id)

    with Timer("find all matches"):
        matches = list(match_od(state, dsl_m_id, dsl_mm_id, pattern_id, ramified_mm_id))


    for match in matches:
        print("\nMATCH:\n", match)

    print(len(matches), 'matches')
