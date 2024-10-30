# Some helper functions

def get_num_ships(od, place):
    place_state = design_to_state(od, place)
    return od.get_slot_value(place_state, "numShips")

def design_to_state(od, design):
    incoming = od.get_incoming(design, "of")
    if len(incoming) == 1:
        # not all design-objects have a state
        return od.get_source(incoming[0])

def state_to_design(od, state):
    return od.get_target(od.get_outgoing(state, "of")[0])
    
def get_time(od):
    _, clock = od.get_all_instances("Clock")[0]
    return clock, od.get_slot_value(clock, "time")
