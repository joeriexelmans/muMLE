from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.common import indent
from concrete_syntax.plantuml import renderer as plantuml
from util.prompt import yes_no, pause
from transformation.cloner import clone_od

state = DevState()

print("Loading meta-meta-model...")
scd_mmm = bootstrap_scd(state)
print("Done")


# Design meta-model
woods_mm_cs = """
    Animal:Class {
        abstract = True;
    }

    Bear:Class
    :Inheritance (Bear -> Animal)

    Man:Class {
        lower_cardinality = 1;
        upper_cardinality = 2;

        constraint = `get_value(get_slot(this, "weight")) > 20`;
    }
    :Inheritance (Man -> Animal)


    Man_weight:AttributeLink (Man -> Integer) {
        name = "weight";
        optional = False;
    }

    afraidOf:Association (Man -> Animal) {
        source_upper_cardinality = 6;
        target_lower_cardinality = 1;
    }
"""

woods_mm = parser.parse_od(
    state,
    m_text=woods_mm_cs,
    mm=scd_mmm)

print("MM valid?")
conf = Conformance(state, woods_mm, scd_mmm)
print(render_conformance_check_result(conf.check_nominal()))

# Runtime meta-model
woods_rt_mm_cs = woods_mm_cs + """
    AnimalState:Class {
        abstract = True;
    }
    AnimalState_dead:AttributeLink (AnimalState -> Boolean) {
        name = "dead";
        optional = False;
    }    
    of:Association (AnimalState -> Animal) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;    
    }

    BearState:Class {
        constraint = `get_type_name(get_target(get_outgoing(this, "of")[0])) == "Bear"`;
    }
    :Inheritance (BearState -> AnimalState)
    BearState_hunger:AttributeLink (BearState -> Integer) {
        name = "hunger";
        optional = False;
        constraint = ```
            val = get_value(get_target(this))
            val >= 0 and val <= 100
        ```;
    }

    ManState:Class {
        constraint = `get_type_name(get_target(get_outgoing(this, "of")[0])) == "Man"`;
    }
    :Inheritance (ManState -> AnimalState)

    Clock:Class {
        lower_cardinality = 1;
        upper_cardinality = 1;
    }
    Clock_time:AttributeLink (Clock -> Integer) {
        name = "time";
        optional = False;
        constraint = `get_value(get_target(this)) >= 0`;
    }
"""

woods_rt_mm = parser.parse_od(
    state,
    m_text=woods_rt_mm_cs,
    mm=scd_mmm)

print("RT-MM valid?")
conf = Conformance(state, woods_rt_mm, scd_mmm)
print(render_conformance_check_result(conf.check_nominal()))

# print("--------------")
# print(indent(
#     renderer.render_od(state,
#         m_id=woods_rt_mm,
#         mm_id=scd_mmm),
#     4))
# print("--------------")

# Our design model - the part that doesn't change
woods_m_cs = """
    george:Man {
        weight = 80;
    }
    bill:Man {
        weight = 70;
    }

    teddy:Bear
    mrBrown:Bear

    # george is afraid of both bears
    :afraidOf (george -> teddy)
    :afraidOf (george -> mrBrown)

    # the men are afraid of each other
    :afraidOf (bill -> george)
    :afraidOf (george -> bill)
"""

woods_m = parser.parse_od(
    state,
    m_text=woods_m_cs,
    mm=woods_mm)

print("M valid?")
conf = Conformance(state, woods_m, woods_mm)
print(render_conformance_check_result(conf.check_nominal()))

# Our runtime model - the part that changes with every execution step
woods_rt_initial_m_cs = woods_m_cs + """
    georgeState:ManState {
        dead = False;
    }
    :of (georgeState -> george)

    billState:ManState {
        dead = False;
    }
    :of (billState -> bill)

    teddyState:BearState {
        dead = False;
        hunger = 20;
    }
    :of (teddyState -> teddy)

    mrBrownState:BearState {
        dead = False;
        hunger = 80;
    }
    :of (mrBrownState -> mrBrown)

    clock:Clock {
        time = 0;
    }
"""

woods_rt_m = parser.parse_od(
    state,
    m_text=woods_rt_initial_m_cs,
    mm=woods_rt_mm)

print("RT-M valid?")
conf = Conformance(state, woods_rt_m, woods_rt_mm)
print(render_conformance_check_result(conf.check_nominal()))

# print("--------------")
# print(indent(
#     renderer.render_od(state,
#         m_id=woods_rt_m,
#         mm_id=woods_rt_mm),
#     4))
# print("--------------")

