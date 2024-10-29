# Design meta-model
port_mm_cs = """
    Source:Class {
        abstract = True;
    }
    Sink:Class {
        abstract = True;
    }

    Place:Class
    :Inheritance (Place -> Source)
    :Inheritance (Place -> Sink)

    connection:Association (Source -> Sink)

    CapacityConstraint:Class

    CapacityConstraint_shipCapacity:AttributeLink (CapacityConstraint -> Integer) {
        name = "shipCapacity";
        optional = False;

        # cannot have negative capacity:
        constraint = `get_value(get_target(this)) >= 0`; # non-negative
    }

    # Capacity 
    capacityOf:Association (CapacityConstraint -> Place) {
        # must say something about at least one Place, otherwise what is the point of the constraint?
        target_lower_cardinality = 1;
    }

    Berth:Class
    :Inheritance (Berth -> Place)

    # Set of workers
    WorkerSet:Class

    WorkerSet_numWorkers:AttributeLink (WorkerSet -> Integer) {
        name = "numWorkers";
        optional = False;
        constraint = `get_value(get_target(this)) >= 0`; # non-negative
    }
    canOperate:Association (WorkerSet -> Berth) {
        target_lower_cardinality = 1;
    }

    Generator:Class
    :Inheritance (Generator -> Source)

    BlackHole:Class
    :Inheritance (BlackHole -> Sink)


    # Those classes to which we want to attach a runtime state object
    Stateful:Class {
        abstract = True;
    }
    :Inheritance (Place      -> Stateful)
    :Inheritance (BlackHole  -> Stateful)
    :Inheritance (WorkerSet  -> Stateful)
    :Inheritance (Berth      -> Stateful)
    :Inheritance (connection -> Stateful)
""";

# Runtime meta-model
port_rt_mm_cs = port_mm_cs + """
    State:Class
    of:Association (State -> Stateful) {
        source_lower_cardinality = 1;
        source_upper_cardinality = 1;
        target_lower_cardinality = 1;
        target_upper_cardinality = 1;
    }

    PlaceState:Class
    :Inheritance (PlaceState -> State)

    PlaceState_numShips:AttributeLink (PlaceState -> Integer) {
        # number of ships currently in the place
        name = "numShips";
        optional = False;
        constraint = `get_value(get_target(this)) >= 0`; # non-negative
    }

    shipCapacities:GlobalConstraint {
        constraint = ```
            errors = []
            for _, constr in get_all_instances("CapacityConstraint"):
                cap = get_slot_value(constr, "shipCapacity")
                total = 0
                place_names = [] # for debugging
                for lnk in get_outgoing(constr, "capacityOf"):
                    place = get_target(lnk)
                    place_names.append(get_name(place))
                    place_state = get_source(get_incoming(place, "of")[0])
                    total += get_slot_value(place_state, "numShips")
                if total > cap:
                    errors.append(f"The number of ships in places {','.join(place_names)} ({total}) exceeds the capacity ({cap}) of CapacityConstraint {get_name(constr)}.")
            errors
        ```;
    }

    BerthState:Class {
        # status == empty <=> numShips == 0
        constraint = `(get_slot_value(this, "numShips") == 0) == (get_slot_value(this, "status") == "empty")`;
    }
    :Inheritance (BerthState -> PlaceState)

    BerthState_status:AttributeLink (BerthState -> String) {
        name = "status";
        optional = False;
        constraint = `(
            get_value(get_target(this)) in { "empty", "unserved", "served" }
        )`;
    }

    WorkerSetState:Class
    :Inheritance (WorkerSetState -> State)

    isOperating:Association (WorkerSetState -> Berth) {
        constraint = ```
            errors = []

            # get status of Berth
            berth = get_target(this)
            berth_state = get_source(get_incoming(berth, "of")[0])
            status = get_slot_value(berth_state, "status")
            if status != "unserved":
                errors.append(f"Cannot operate {get_name(berth)} because there is no unserved ship there.")

            # only operate Berts that we can operate
            workerset = get_target(get_outgoing(get_source(this), "of")[0])
            can_operate = [get_target(lnk) for lnk in get_outgoing(workerset, "canOperate")]
            if berth not in can_operate:
                errors.append(f"Cannot operate {get_name(berth)}.")

            errors
        ```;
    }

    operatingCapacities:GlobalConstraint {
        constraint = ```
            errors = []
            for _, workersetstate in get_all_instances("WorkerSetState"):
                workerset = get_target(get_outgoing(workersetstate, "of")[0])
                num_operating = len(get_outgoing(workersetstate, "isOperating"))
                num_workers = get_slot_value(workerset, "numWorkers")
                if num_operating > num_workers:
                    errors.append(f"WorkerSet {get_name(workerset)} is operating more berths ({num_operating}) than there are workers ({num_workers})")
            errors
        ```;
    }

    ConnectionState:Class
    :Inheritance (ConnectionState -> State)
    ConnectionState_moved:AttributeLink (ConnectionState -> Boolean) {
        name = "moved";
        optional = False;
        constraint = ```
            all_successors_moved = True
            moved = get_value(get_target(this))
            conn_state = get_source(this)
            conn = get_target(get_outgoing(conn_state, "of")[0])
            tgt_place = get_target(conn)
            next_conns = get_outgoing(tgt_place, "connection")
            for next_conn in next_conns:
                next_conn_state = get_source(get_incoming(next_conn, "of")[0])
                if not get_slot_value(next_conn_state, "moved"):
                    all_successors_moved = False
            not moved or all_successors_moved
        ```;
    }

    BlackHoleState:Class
    :Inheritance (BlackHoleState -> State)
    BlackHoleState_counter:AttributeLink (BlackHoleState -> Integer) {
        name = "counter";
        optional = False;
        constraint = `get_value(get_target(this)) >= 0`; # non-negative
    }

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

# Design model: the part that doesn't change
port_m_cs = """
    gen:Generator

    # newly arrive ships collect here
    waiting:Place
    c1:connection (gen -> waiting)

    inboundPassage:Place
    c2:connection (waiting -> inboundPassage)

    outboundPassage:Place

    # inboundPassage and outboundPassage cannot have more than 3 ships total
    passageCap:CapacityConstraint {
        shipCapacity = 3;
    }
    :capacityOf (passageCap -> inboundPassage)
    :capacityOf (passageCap -> outboundPassage)


    # Berth 1

    inboundBerth1:Place
    berth1:Berth
    outboundBerth1:Place

    inboundBerth1Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (inboundBerth1Cap -> inboundBerth1)
    outboundBerth1Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (outboundBerth1Cap -> outboundBerth1)

    berth1Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (berth1Cap -> berth1)

    c3:connection (inboundBerth1 -> berth1)
    c4:connection (berth1 -> outboundBerth1)

    # Berth 2

    inboundBerth2:Place
    berth2:Berth
    outboundBerth2:Place

    inboundBerth2Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (inboundBerth2Cap -> inboundBerth2)
    outboundBerth2Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (outboundBerth2Cap -> outboundBerth2)

    berth2Cap:CapacityConstraint { shipCapacity = 1; }
    :capacityOf (berth2Cap -> berth2)

    c5:connection (inboundBerth2 -> berth2)
    c6:connection (berth2 -> outboundBerth2)


    # can either go to Berth 1 or Berth 2
    c7:connection (inboundPassage -> inboundBerth1)
    c8:connection (inboundPassage -> inboundBerth2)

    c9:connection (outboundBerth1 -> outboundPassage)
    c10:connection (outboundBerth2 -> outboundPassage)


    # ships that have been served are counted here
    served:BlackHole
    c11:connection (outboundPassage -> served)


    workers:WorkerSet {
        numWorkers = 1;
    }
    :canOperate (workers -> berth1)
    :canOperate (workers -> berth2)
"""

# Initial runtime model: the part that changes (every execution step)
port_rt_m_cs = port_m_cs + """
    clock:Clock {
        time = 0;
    }

    waitingState:PlaceState         { numShips = 2; }  :of (waitingState -> waiting)
    inboundPassageState:PlaceState  { numShips = 0; }  :of (inboundPassageState -> inboundPassage)
    outboundPassageState:PlaceState { numShips = 0; }  :of (outboundPassageState -> outboundPassage)

    inboundBerth1State:PlaceState   { numShips = 0; }  :of (inboundBerth1State -> inboundBerth1)
    outboundBerth1State:PlaceState  { numShips = 0; }  :of (outboundBerth1State -> outboundBerth1)
    inboundBerth2State:PlaceState   { numShips = 0; }  :of (inboundBerth2State -> inboundBerth2)
    outboundBerth2State:PlaceState  { numShips = 0; }  :of (outboundBerth2State -> outboundBerth2)

    berth1State:BerthState { status = "empty"; numShips = 0; }  :of (berth1State -> berth1)
    berth2State:BerthState { status = "empty"; numShips = 0; }  :of (berth2State -> berth2)

    servedState:BlackHoleState { counter = 0; }  :of (servedState -> served)

    workersState:WorkerSetState  :of (workersState -> workers)

    c1S:ConnectionState  { moved = False; }   :of (c1S -> c1)
    c2S:ConnectionState  { moved = False; }   :of (c2S -> c2)
    c3S:ConnectionState  { moved = False; }   :of (c3S -> c3)
    c4S:ConnectionState  { moved = False; }   :of (c4S -> c4)
    c5S:ConnectionState  { moved = False; }   :of (c5S -> c5)
    c6S:ConnectionState  { moved = False; }   :of (c6S -> c6)
    c7S:ConnectionState  { moved = False; }   :of (c7S -> c7)
    c8S:ConnectionState  { moved = False; }   :of (c8S -> c8)
    c9S:ConnectionState  { moved = False; }   :of (c9S -> c9)
    c10S:ConnectionState { moved = False; }   :of (c10S -> c10)
    c11S:ConnectionState { moved = False; }   :of (c11S -> c11)
"""
