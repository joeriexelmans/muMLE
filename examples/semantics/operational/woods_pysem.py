import functools
import random
import math

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser, renderer
from concrete_syntax.common import indent
from concrete_syntax.plantuml import renderer as plantuml
from util import prompt
from transformation.cloner import clone_od
from api.od import ODAPI

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

    attacking:Association (AnimalState -> ManState) {
        # Animal can only attack one Man at a time
        target_upper_cardinality = 1;

        # Man can only be attacked by one Animal at a time
        source_upper_cardinality = 1;

        constraint = ```
            attacker = get_source(this)
            if get_type_name(attacker) == "BearState":
                # only BearState has 'hunger' attribute
                hunger = get_value(get_slot(attacker, "hunger"))
            else:
                hunger = 100 # Man can always attack
            attacker_dead = get_value(get_slot(attacker, "dead"))
            attacked_state = get_target(this)
            attacked_dead = get_value(get_slot(attacked_state, "dead"))
            (
                hunger >= 50 
                and not attacker_dead # cannot attack while dead
                and not attacked_dead # cannot attack whoever is dead
            )
        ```;
    }

    attacking_starttime:AttributeLink (attacking -> Integer) {
        name = "starttime";
        optional = False;
        constraint = ```
            val = get_value(get_target(this))
            _, clock = get_all_instances("Clock")[0]
            current_time = get_slot_value(clock, "time")
            val >= 0 and val <= current_time
        ```;
    }

    # Just a clock singleton for keeping the time
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
        hunger = 40;
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


# Helpers
def state_of(od, animal):
    return od.get_source(od.get_incoming(animal, "of")[0])
def animal_of(od, state):
    return od.get_target(od.get_outgoing(state, "of")[0])
def get_time(od):
    _, clock = od.get_all_instances("Clock")[0]
    return clock, od.get_slot_value(clock, "time")

def advance_time(od):
    msgs = []
    clock, old_time = get_time(od)
    new_time = old_time + 1
    od.set_slot_value(clock, "time", new_time)

    for _, attacking_link in od.get_all_instances("attacking"):
        man_state = od.get_target(attacking_link)
        animal_state = od.get_source(attacking_link)
        if od.get_type_name(animal_state) == "BearState":
            od.set_slot_value(animal_state, "hunger", max(od.get_slot_value(animal_state, "hunger") - 50, 0))
        od.set_slot_value(man_state, "dead", True)
        od.delete(attacking_link)
        msgs.append(f"{od.get_name(animal_of(od, animal_state))} kills {od.get_name(animal_of(od, man_state))}.")

    for _, bear_state in od.get_all_instances("BearState"):
        if od.get_slot_value(bear_state, "dead"):
            continue # bear already dead
        old_hunger = od.get_slot_value(bear_state, "hunger")
        new_hunger = min(old_hunger + 5, 100)
        od.set_slot_value(bear_state, "hunger", new_hunger)
        bear = od.get_target(od.get_outgoing(bear_state, "of")[0])
        bear_name = od.get_name(bear)
        if new_hunger == 100:
            od.set_slot_value(bear_state, "dead", True)
            msgs.append(f"Bear {bear_name} dies of hunger.")
        else:
            msgs.append(f"Bear {bear_name}'s hunger level is now {new_hunger}.")
    return msgs

# we must use the names of the objects as parameters, because when cloning, the IDs of objects change!
def attack(od, animal_name: str, man_name: str):
    msgs = []
    animal = od.get(animal_name)
    man = od.get(man_name)
    animal_state = state_of(od, animal)
    man_state = state_of(od, man)
    attack_link = od.create_link(None, # auto-generate link name
        "attacking", animal_state, man_state)
    _, clock = od.get_all_instances("Clock")[0]
    current_time = od.get_slot_value(clock, "time")
    od.set_slot_value(attack_link, "starttime", current_time)
    msgs.append(f"{animal_name} is now attacking {man_name}")
    return msgs

def get_actions(od):
    # can always advance time:
    actions = { "advance time": advance_time }

    # who can attack whom?
    for _, afraid_link in od.get_all_instances("afraidOf"):
        man = od.get_source(afraid_link)
        animal = od.get_target(afraid_link)
        animal_name = od.get_name(animal)
        man_name = od.get_name(man)
        man_state = state_of(od, man)
        animal_state = state_of(od, animal)
        descr = f"{animal_name} ({od.get_type_name(animal)}) attacks {man_name} ({od.get_type_name(man)})"
        actions[descr] = functools.partial(attack, animal_name=animal_name, man_name=man_name)
        
    return { action_descr: functools.partial(exec_pure, action, od) for action_descr, action in actions.items() }

# Copy model before modifying it
def exec_pure(action, od):
    cloned_rt_m = clone_od(state, od.m, od.mm)
    new_od = ODAPI(state, cloned_rt_m, od.mm)
    msgs = action(new_od)
    return (new_od, msgs)

def filter_actions(actions):
    result = {}
    def make_tuple(new_od, msgs):
        return (new_od, msgs)
    for name, callback in actions.items():
        print(f"attempt '{name}' ...", end='\r')
        (new_od, msgs) = callback()
        conf = Conformance(state, new_od.m, new_od.mm)
        errors = conf.check_nominal()
        # erase current line:
        print("                                                  ", end='\r')
        if len(errors) == 0:
            # updated RT-M is conform, we have a valid action:
            yield (name, functools.partial(make_tuple, new_od, msgs))

def unfilter_actions(actions, od):
    for name, callback in actions.items():
        yield (name, callback)

def render_woods(od):
    txt = ""
    _, time = get_time(od)
    txt += f"T = {time}.\n"
    txt += "Bears:\n"
    def render_attacking(animal_state):
        attacking = od.get_outgoing(animal_state, "attacking")
        if len(attacking) == 1:
            whom_state = od.get_target(attacking[0])
            whom_name = od.get_name(animal_of(od, whom_state))
            return f" attacking {whom_name}"
        else:
            return ""
    def render_dead(animal_state):
        return 'dead' if od.get_slot_value(animal_state, 'dead') else 'alive'
    for _, bear_state in od.get_all_instances("BearState"):
        bear = animal_of(od, bear_state)
        hunger = od.get_slot_value(bear_state, "hunger")
        txt += f"  🐻 {od.get_name(bear)} (hunger: {hunger}, {render_dead(bear_state)}) {render_attacking(bear_state)}\n"
    txt += "Men:\n"
    for _, man_state in od.get_all_instances("ManState"):
        man = animal_of(od, man_state)
        attacked_by = od.get_incoming(man_state, "attacking")
        if len(attacked_by) == 1:
            whom_state = od.get_source(attacked_by[0])
            whom_name = od.get_name(animal_of(od, whom_state))
            being_attacked = f" being attacked by {whom_name}"
        else:
            being_attacked = ""
        txt += f"  👨 {od.get_name(man)} ({render_dead(man_state)}) {render_attacking(man_state)}{being_attacked}\n"
    return txt

od = ODAPI(state, woods_rt_m, woods_rt_mm)

RANDOM_SEED = 0

r = random.Random(RANDOM_SEED)

def random_choice(options):
    arr = [action for descr, action in options]
    i = math.floor(r.random()*len(arr))
    return arr[i]

def termination_condition(od):
    _, time = get_time(od)
    return time >= 10 # stop after 10 steps

print(f"Using random seed: {RANDOM_SEED} (only applicable to random simulation)")

while True:
    print("--------------")
    print(indent(render_woods(od), 4))
    print("--------------")

    if termination_condition(od):
        print("Termination condition satisfied. Quit.")
        break

    # print(indent(
    #     renderer.render_od(state,
    #         m_id=od.m,
    #         mm_id=od.mm),
    #     4))

    # 1. Only 'valid' actions or all actions?
    # actions = unfilter_actions(get_actions(od), od)
    actions = filter_actions(get_actions(od))

    # 2. Manual or random selection?
    # action = prompt.choose("Select action:", actions)
    action = random_choice(actions)

    if action == None:
        print("No enabled actions. Quit.")
        break

    (od, msgs) = action()
    print(indent('\n'.join(f"▸ {msg}" for msg in msgs), 2))

    print()
    conf = Conformance(state, od.m, od.mm)
    print(render_conformance_check_result(conf.check_nominal()))
