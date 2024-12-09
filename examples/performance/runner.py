# Artificial model transformation thingy to measure performance
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
        ass:Association(Many->ManyB)
        ass2:Association(Rare->Many)
    """
    dsl_mm_id = parser.parse_od(state, dsl_mm_cs, mm=scd_mmm_id)
    
    dsl_m_cs = """
        rare:Rare

        many0:Many
        many0B:Many
        many1:Many
        many1B:Many
        many2:Many
        many2B:Many
        many3:Many
        many3B:Many
        many4:Many
        many4B:Many

        many5:ManyB
        many6:ManyB
        many7:ManyB
        many8:ManyB
        many50:ManyB
        many60:ManyB
        many70:ManyB
        many80:ManyB
        many51:ManyB
        many61:ManyB
        many71:ManyB
        many81:ManyB
        many501:ManyB
        many601:ManyB
        many701:ManyB
        many801:ManyB
        many5Z:ManyB
        many6Z:ManyB
        many7Z:ManyB
        many8Z:ManyB
        many50Z:ManyB
        many60Z:ManyB
        many70Z:ManyB
        many80Z:ManyB
        many51Z:ManyB
        many61Z:ManyB
        many71Z:ManyB
        many81Z:ManyB
        many501Z:ManyB
        many601Z:ManyB
        many701Z:ManyB
        many801Z:ManyB

        Other0:Other
        Other1:Other
        Other2:Other
        Other3:Other
        Other0B:Other
        Other1B:Other
        Other2B:Other
        Other3B:Other
        Other0C:Other
        Other1C:Other
        Other2C:Other
        Other3C:Other

        :ass (many2->many6)
        :ass (many3->many8)

        :ass2 (rare -> many0)
        :ass2 (rare -> many1)
        :ass2 (rare -> many2)
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
        rare:RAM_Rare {{
        }}

        many:RAM_Many
        manyB:RAM_ManyB
        manyB2:RAM_ManyB

        :RAM_ass (many -> manyB)
        :RAM_ass (many -> manyB2)
        :RAM_ass2 (rare -> many)
    """
    pattern_id = parser.parse_od(state, pattern_cs, mm=ramified_mm_id)

    with Timer("find all matches"):
        for i in range(100):
            matches = list(match_od(state, dsl_m_id, dsl_mm_id, pattern_id, ramified_mm_id))


    for match in matches:
        print("\nMATCH:\n", match)

    print(len(matches), 'matches')
