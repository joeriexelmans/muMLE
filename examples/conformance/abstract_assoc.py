from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.common import indent
from concrete_syntax.plantuml import renderer as plantuml
from util.prompt import yes_no, pause

state = DevState()
scd_mmm = bootstrap_scd(state)


# Change this:
mm_cs = """
    BaseA:Class {
        abstract = True;
    }
    BaseB:Class {
        abstract = True;
    }
    baseAssoc:Association (BaseA -> BaseB) {
        abstract = True;
        target_lower_cardinality = 1;
        target_upper_cardinality = 2; # A has 1..2 B
    }
    A:Class
    B:Class
    assoc:Association (A -> B) {
        # we can further restrict cardinality from baseAssoc:
        target_upper_cardinality = 1;

        # relaxing cardinalities or constraints can be done (meaning: it will still be a valid meta-model), but will have no effect: for any instance of a type, the constraints defined on the type and its supertypes will be checked.
    }
    :Inheritance (A -> BaseA)
    :Inheritance (B -> BaseB)
    :Inheritance (assoc -> baseAssoc)
"""

print()
print("Parsing meta-model...")
mm = parser.parse_od(
    state,
    m_text=mm_cs, # the string of text to parse
    mm=scd_mmm, # the meta-model of class diagrams (= our meta-meta-model)
)
print("OK")

print("Is our meta-model a valid class diagram?")
conf = Conformance(state, mm, scd_mmm)
print(render_conformance_check_result(conf.check_nominal()))

# Change this:
m_cs = """
    a0:A
    b0:B
    b1:B

    # error: assoc (A -> B) must have tgt card 0..1 (and we have 2 instead)
    :assoc (a0 -> b0)
    :assoc (a0 -> b1)

    # error: baseAssoc (A -> B) must have tgt card 1..2 (and we have 0 instead)
    a1:A
"""

print()
print("Parsing model...")
m = parser.parse_od(
    state,
    m_text=m_cs,
    mm=mm, # this time, the meta-model is the previous model we parsed
)
print("OK")

print("Is our model a valid woods-diagram?")
conf = Conformance(state, m, mm)
print(render_conformance_check_result(conf.check_nominal()))
