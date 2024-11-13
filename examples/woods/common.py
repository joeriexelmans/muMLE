# Helpers
def state_of(od, animal):
    return od.get_source(od.get_incoming(animal, "of")[0])
def animal_of(od, state):
    return od.get_target(od.get_outgoing(state, "of")[0])
def get_time(od):
    _, clock = od.get_all_instances("Clock")[0]
    return clock, od.get_slot_value(clock, "time")


# Render our run-time state to a string
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


# When should simulation stop?
def termination_condition(od):
    _, time = get_time(od)
    if time >= 10:
        return "Took too long"

    # End simulation when 2 animals are dead
    who_is_dead = []
    for _, animal_state in od.get_all_instances("AnimalState"):
        if od.get_slot_value(animal_state, "dead"):
            animal_name = od.get_name(animal_of(od, animal_state))
            who_is_dead.append(animal_name)
    if len(who_is_dead) >= 2:
        return f"{' and '.join(who_is_dead)} are dead"
