### Operational Semantics - coded in Python ###

import functools
from examples.semantics.operational.simulator import make_actions_pure, filter_valid_actions
from examples.woods.common import *

# Action: Time advances, whoever is being attacked dies, bears become hungrier
def action_advance_time(od):
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
        new_hunger = min(old_hunger + 10, 100)
        od.set_slot_value(bear_state, "hunger", new_hunger)
        bear = od.get_target(od.get_outgoing(bear_state, "of")[0])
        bear_name = od.get_name(bear)
        if new_hunger == 100:
            od.set_slot_value(bear_state, "dead", True)
            msgs.append(f"Bear {bear_name} dies of hunger.")
        else:
            msgs.append(f"Bear {bear_name}'s hunger level is now {new_hunger}.")
    return msgs

# Action: Animal attacks Man
# Note: We must use the names of the objects as parameters, because when cloning, the IDs of objects change!
def action_attack(od, animal_name: str, man_name: str):
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

# Get all actions that can be performed (including those that bring us to a non-conforming state)
def get_all_actions(od):
    def _generate_actions(od):
        # can always advance time:
        yield ("advance time", action_advance_time)

        # if A is afraid of B, then B can attack A:
        for _, afraid_link in od.get_all_instances("afraidOf"):
            man = od.get_source(afraid_link)
            animal = od.get_target(afraid_link)
            animal_name = od.get_name(animal)
            man_name = od.get_name(man)
            man_state = state_of(od, man)
            animal_state = state_of(od, animal)
            descr = f"{animal_name} ({od.get_type_name(animal)}) attacks {man_name} ({od.get_type_name(man)})"
            yield (descr, functools.partial(action_attack, animal_name=animal_name, man_name=man_name))

    return make_actions_pure(_generate_actions(od), od)

# Only get those actions that bring us to a conforming state
def get_valid_actions(od):
    return filter_valid_actions(get_all_actions(od))
