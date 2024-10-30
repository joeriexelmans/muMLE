import functools
from concrete_syntax.common import indent
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time
from examples.semantics.operational.simulator import make_actions_pure, filter_valid_actions


def precondition_can_move_from(od, from_state):

    # TO IMPLEMENT

    # Function should return True if a ship can move out of 'from_state'

    return False

def precondition_can_move_to(od, to_state):

    # TO IMPLEMENT

    # Function should return True if a ship can move into 'to_state'

    return False

def precondition_all_successors_moved(od, conn):

    # TO IMPLEMENT

    # A move (or skip) can only be made along a connection after all subsequent connections have already made their move (or were skipped).

    return True

def precondition_workers_available(od, workerset):

    # TO IMPLEMENT

    # A worker in a WorkerSet can only be allocated to a berth, if the number of 'isOperating'-links is smaller than the number of workers in the WorkerSet.

    return True

def precondition_berth_unserved(od, berth):

    # TO IMPLEMENT

    # A worker can only be allocated to a berth, if the berth contains an 'unserved' ship.

    return True

def action_skip(od, conn_name):
    # SERVES AS AN EXAMPLE - NO NEED TO EDIT THIS FUNCTION
    conn = od.get(conn_name)
    conn_state = design_to_state(od, conn)
    od.set_slot_value(conn_state, "moved", True)
    return [f"skip {conn_name}"]

def action_move(od, conn_name):
    action_skip(od, conn_name) # flag the connection as 'moved'

    conn = od.get(conn_name)
    from_place = od.get_source(conn)
    to_place = od.get_target(conn)

    from_state = design_to_state(od, from_place) # beware: Generator does not have State
    to_state = design_to_state(od, to_place)

    # TO IMPLEMENT:
    #  - move a ship along the connection

    return [f"unimplemented! nothing changed!"]

def action_serve_berth(od, workerset_name, berth_name):

    # TO IMPLEMENT:
    #  - A worker starts operating a berth

    return [f"unimplemented! nothing changed!"]

def action_advance_time(od):
    _, clock = od.get_all_instances("Clock")[0]
    time = od.get_slot_value(clock, "time")
    new_time = time + 1
    od.set_slot_value(clock, "time", new_time)

    # TO IMPLEMENT:
    #  - all 'moved'-attributes need to be reset (to False)
    #  - if there is a worker operating a Berth, then:
    #      (1) the Berth's status becomes 'served'
    #      (2) the worker is no longer operating the Berth

    return [f"time is now {new_time}"]

# This function is called to discover the possible steps that can be made.
# It should not be necessary to edit this function
def get_actions(od):
    actions = {}

    # Add move-actions (or skip-actions)
    for conn_name, conn in od.get_all_instances("connection"):
        already_moved = od.get_slot_value(design_to_state(od, conn), "moved")
        if already_moved or not precondition_all_successors_moved(od, conn):
            # a move was already made along this connection in the current time-step
            continue

        from_place = od.get_source(conn)
        to_place = od.get_target(conn)
        from_name = od.get_name(from_place)
        to_name = od.get_name(to_place)
        from_state = design_to_state(od, from_place)
        to_state = design_to_state(od, to_place)

        if (precondition_can_move_from(od, from_state)
          and precondition_can_move_to(od, to_state)):
            actions[f"move {conn_name} ({from_name} -> {to_name})"] = functools.partial(action_move, conn_name=conn_name)
        else:
            actions[f"skip {from_name} -> {to_name}"] = functools.partial(action_skip, conn_name=conn_name)

    # Add actions to assign workers
    for _, workerset in od.get_all_instances("WorkerSet"):
        if not precondition_workers_available(od, workerset):
            continue
        for lnk in od.get_outgoing(workerset, "canOperate"):
            berth = od.get_target(lnk)
            if precondition_berth_unserved(od, berth):
                berth_name = od.get_name(berth)
                workerset_name = od.get_name(workerset)
                actions[f"{workerset_name} operates {berth_name}"] = functools.partial(action_serve_berth, workerset_name=workerset_name, berth_name=berth_name)

    # Only when no other action can be performed, can time advance
    if len(actions) == 0:
        actions["advance time"] = action_advance_time

    # This wrapper turns our actions into pure functions: they will clone the model before modifying it. This is useful if we ever want to rollback an action.
    return make_actions_pure(actions.items(), od)


# Called every time the runtime state changes.
# When this function returns a string, the simulation ends.
# The string should represent the reason for ending the simulation.
# When this function returns None, the simulation continues.
def termination_condition(od):

    # TO IMPLEMENT: terminate simulation when the place 'served' contains 2 ships.

    if len(od.get_all_instances("Place")) > 5:
        return "More places than I can count :("

