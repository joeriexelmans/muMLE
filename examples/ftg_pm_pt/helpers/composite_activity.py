from uuid import UUID

from api.od import ODAPI
from examples.ftg_pm_pt.ftg_pm_pt import FtgPmPt
from examples.ftg_pm_pt.runner import FtgPmPtRunner


def find_previous_artefact(od: ODAPI, linked_artefacts):
    return next((od.get_source(link) for link in linked_artefacts if
                 not od.get_incoming(od.get_source(link), "pt_PrevVersion")), None)


def create_activity_links(od: ODAPI, activity, prev_element, ctrl_port, end_trace=None,
                          relation_type="pt_IsFollowedBy"):
    od.create_link(None, "pt_RelatesTo", activity, ctrl_port)
    od.create_link(None, relation_type, prev_element, activity)
    if end_trace:
        od.create_link(None, "pt_IsFollowedBy", activity, end_trace)


def get_workflow_path(od: ODAPI, activity: UUID):
    return od.get_slot_value(activity, "subworkflow_path")


def get_workflow(workflow_path: str):
    with open(workflow_path, "r") as f:
        return f.read()


############################

def get_runtime_state(od: ODAPI, design_obj: UUID):
    states = od.get_incoming(design_obj, "pm_Of")
    if len(states) == 0:
        print(f"Design object '{od.get_name(design_obj)}' has no runtime state.")
        return None
    return od.get_source(states[0])


def get_source_incoming(od: ODAPI, obj: UUID, link_name: str):
    links = od.get_incoming(obj, link_name)
    if len(links) == 0:
        print(f"Object '{od.get_name(obj)} has no incoming links of type '{link_name}'.")
        return None
    return od.get_source(links[0])


def get_target_outgoing(od: ODAPI, obj: UUID, link_name: str):
    links = od.get_outgoing(obj, link_name)
    if len(links) == 0:
        print(f"Object '{od.get_name(obj)} has no outgoing links of type '{link_name}'.")
        return None
    return od.get_target(links[0])


def set_control_port_value(od: ODAPI, port: UUID, value: bool):
    state = get_runtime_state(od, port)
    od.set_slot_value(state, "active", value)


def set_artefact_data(od: ODAPI, artefact: UUID, value: bytes):
    state = artefact
    # Only the proces model of the artefact contains a runtime state
    if od.get_type_name(state) == "pm_Artefact":
        state = get_runtime_state(od, artefact)
    od.set_slot_value(state, "data", value)


def get_artefact_data(od: ODAPI, artefact):
    state = artefact
    # Only the proces model of the artefact contains a runtime state
    if od.get_type_name(state) == "pm_Artefact":
        state = get_runtime_state(od, artefact)
    return od.get_slot_value(state, "data")


############################

def set_workflow_control_source(workflow_model: FtgPmPt, ctrl_port_name: str, composite_linkage: dict):
    od = workflow_model.odapi
    source_port_name = composite_linkage[ctrl_port_name]
    source_port = od.get(source_port_name)
    set_control_port_value(od, source_port, True)


def set_workflow_artefacts(act_od: ODAPI, activity: UUID, workflow_model: FtgPmPt, composite_linkage: dict):
    for data_port in [act_od.get_target(data_in) for data_in in act_od.get_outgoing(activity, "pm_HasDataIn")]:
        # Get the data source port of the inner workflow
        data_port_name = act_od.get_name(data_port)
        source_port_name = composite_linkage[data_port_name]
        source_port = workflow_model.odapi.get(source_port_name)

        # Get the artefact that is linked to the data port of the activity
        act_artefact = get_source_incoming(act_od, data_port, "pm_DataFlowOut")
        # Get the data of the artefact
        artefact_data = get_artefact_data(act_od, act_artefact)

        # Get the artefact that is linked to the data port of the inner workflow
        workflow_artefact = get_target_outgoing(workflow_model.odapi, source_port, "pm_DataFlowIn")
        set_artefact_data(workflow_model.odapi, workflow_artefact, artefact_data)


def get_activity_port_from_inner_port(composite_linkage: dict, port_name: str):
    for act_port_name, work_port_name in composite_linkage.items():
        if work_port_name == port_name:
            return act_port_name


def execute_composite_workflow(od: ODAPI, activity: UUID, ctrl_port: UUID, composite_linkage: dict,
                               packages: dict | None, matched=None):
    activity_name = od.get_slot_value(activity, "name")

    # First get the path of the object diagram file that contains the inner workflow of the activity
    workflow_path = get_workflow_path(od, activity)

    # Read the object diagram file
    workflow = get_workflow(workflow_path)

    # Create an FtgPmPt object
    workflow_model = FtgPmPt(activity_name)

    # Load the workflow to the object
    workflow_model.load_model(workflow)

    # Set the correct control source port of the workflow to active
    set_workflow_control_source(workflow_model, od.get_name(ctrl_port), composite_linkage[activity_name])

    # If a data port is linked, set the data of the artefact
    set_workflow_artefacts(od, activity, workflow_model, composite_linkage[activity_name])

    # Create an FtgPmPtRunner object with the FtgPmPt object
    workflow_runner = FtgPmPtRunner(workflow_model)

    # Set the packages if present
    workflow_runner.set_packages(packages, is_path=False)

    # Run the FtgPmPtRunner (is a subprocess necessary? This makes it more complicated because now we have direct access to the object)
    workflow_runner.run()

    # Contains all the ports of the inner workflow -> map back to the activity ports, and so we can set the correct
    # Control ports to active and also set the data artefacts correctly
    ports = extract_inner_workflow(workflow_model.odapi)
    start_act = None
    end_act = None
    for port in [port for port in ports if port]:
        port_name = workflow_model.odapi.get_name(port)
        activity_port_name = get_activity_port_from_inner_port(composite_linkage[activity_name], port_name)
        activity_port = od.get(activity_port_name)
        match workflow_model.odapi.get_type_name(port):
            case "pm_CtrlSource":
                start_act = handle_control_source(od, activity_port, matched("prev_trace_element"))
            case "pm_CtrlSink":
                end_act = handle_control_sink(od, activity_port, start_act, matched("end_trace"))
            case "pm_DataSource":
                handle_data_source(od, activity_port, start_act)
            case "pm_DataSink":
                handle_data_sink(od, workflow_model.odapi, activity_port, port, end_act)


def handle_control_source(od: ODAPI, port, prev_trace_elem):
    set_control_port_value(od, port, False)
    start_activity = od.create_object(None, "pt_StartActivity")
    create_activity_links(od, start_activity, prev_trace_elem, port)
    return start_activity


def handle_control_sink(od: ODAPI, port, start_act, end_trace):
    set_control_port_value(od, port, True)
    end_activity = od.create_object(None, "pt_EndActivity")
    create_activity_links(od, end_activity, start_act, port, end_trace)
    return end_activity


def handle_data_source(od: ODAPI, port, start_activity):
    pt_artefact = od.create_object(None, "pt_Artefact")
    od.create_link(None, "pt_Consumes", pt_artefact, start_activity)

    pm_artefact = get_source_incoming(od, port, "pm_DataFlowOut")
    pm_artefact_data = get_artefact_data(od, pm_artefact)
    set_artefact_data(od, pt_artefact, pm_artefact_data)
    prev_pt_artefact = find_previous_artefact(od, od.get_incoming(pm_artefact, "pt_BelongsTo"))
    if prev_pt_artefact:
        od.create_link(None, "pt_PrevVersion", pt_artefact, prev_pt_artefact)
    od.create_link(None, "pt_BelongsTo", pt_artefact, pm_artefact)


def handle_data_sink(act_od: ODAPI, work_od: ODAPI, act_port, work_port, end_activity):
    pt_artefact = act_od.create_object(None, "pt_Artefact")
    act_od.create_link(None, "pt_Produces", end_activity, pt_artefact)

    work_artefact = get_source_incoming(work_od, work_port, "pm_DataFlowOut")
    work_artefact_data = get_artefact_data(work_od, work_artefact)

    act_artefact = get_target_outgoing(act_od, act_port, "pm_DataFlowIn")

    set_artefact_data(act_od, act_artefact, work_artefact_data)
    set_artefact_data(act_od, pt_artefact, work_artefact_data)

    prev_pt_artefact = find_previous_artefact(act_od, act_od.get_incoming(act_artefact, "pt_BelongsTo"))
    if prev_pt_artefact:
        act_od.create_link(None, "pt_PrevVersion", pt_artefact, prev_pt_artefact)
    act_od.create_link(None, "pt_BelongsTo", pt_artefact, act_artefact)


def extract_inner_workflow(workflow: ODAPI):
    # Get the model, this should be only one
    name, model = workflow.get_all_instances("pm_Model")[0]

    # Get the start of the process trace
    start_trace = get_source_incoming(workflow, model, "pt_Starts")
    # Get the end of the process trace
    end_trace = get_source_incoming(workflow, model, "pt_Ends")

    # Get the first started activity
    first_activity = get_target_outgoing(workflow, start_trace, "pt_IsFollowedBy")
    # Get the last ended activity
    end_activity = get_source_incoming(workflow, end_trace, "pt_IsFollowedBy")

    # Get the control port that started the activity
    act_ctrl_in = get_target_outgoing(workflow, first_activity, "pt_RelatesTo")
    # Get the control port that is activated when the activity is executed
    act_ctrl_out = get_target_outgoing(workflow, end_activity, "pt_RelatesTo")

    # Get the control source of the workflow
    ports = []
    for port in workflow.get_incoming(act_ctrl_in, "pm_CtrlFlow"):
        source = workflow.get_source(port)
        if workflow.get_type_name(source) == "pm_CtrlSource":
            # Only one port can activate an activity
            ports.append(source)
            break

    # Get the control sink of the workflow
    for port in workflow.get_outgoing(act_ctrl_out, "pm_CtrlFlow"):
        sink = workflow.get_target(port)
        if workflow.get_type_name(sink) == "pm_CtrlSink":
            # Only one port can be set to active one an activity is ended
            ports.append(sink)
            break

    # Get the data port that the activity consumes (if used)
    consumed_links = workflow.get_incoming(first_activity, "pt_Consumes")
    if len(consumed_links) > 0:
        pt_artefact = None
        for link in consumed_links:
            pt_artefact = workflow.get_source(link)
            # Check if it is the first artefact -> contains no previous version
            if len(workflow.get_outgoing(pt_artefact, "pt_PrevVersion")) == 0:
                break

        pm_artefact = get_target_outgoing(workflow, pt_artefact, "pt_BelongsTo")
        # Find the data source port
        for link in workflow.get_incoming(pm_artefact, "pm_DataFlowIn"):
            source = workflow.get_source(link)
            if workflow.get_type_name(source) == "pm_DataSource":
                # An activity can only use one artefact as input
                ports.append(source)
                break

    # Get all data ports that are connected to an artefact that is produced by an activity in the workflow,
    # where the artefact is also part of main workflow
    for port_name, data_sink in workflow.get_all_instances("pm_DataSink"):
        pm_art = get_source_incoming(workflow, data_sink, "pm_DataFlowOut")
        # If the pm_artefact is linked to a proces trace artefact that is produced, we can add to port
        links = workflow.get_incoming(pm_art, "pt_BelongsTo")
        if not len(links):
            continue
        # A data sink port linkage will only be added to the proces trace when an activity is ended and so an artefact
        # is produced, meaning that if a belongsTo link exists, a proces trace artefact is linked to this data port
        ports.append(data_sink)

    return ports
