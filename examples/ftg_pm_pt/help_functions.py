import copy
import pickle

from api.od import ODAPI

from examples.ftg_pm_pt.helpers.composite_activity import execute_composite_workflow

def serialize(obj):
    return pickle.dumps(obj)


def deserialize(obj):
    return pickle.loads(obj)


def create_activity_links(od: ODAPI, activity, prev_element, ctrl_port, end_trace=None,
                          relation_type="pt_IsFollowedBy"):
    od.create_link(None, "pt_RelatesTo", activity, ctrl_port)
    od.create_link(None, relation_type, prev_element, activity)
    if end_trace:
        od.create_link(None, "pt_IsFollowedBy", activity, end_trace)


def extract_input_data(od: ODAPI, activity):
    input_data = {}
    for has_data_in in od.get_outgoing(activity, "pm_HasDataIn"):
        data_port = od.get_target(has_data_in)
        artefact_state = od.get_source(od.get_incoming(od.get_source(od.get_incoming(data_port, "pm_DataFlowOut")[0]), "pm_Of")[0])
        input_data[od.get_name(data_port)] = deserialize(od.get_slot_value(artefact_state, "data"))
    return input_data


def execute_activity(od: ODAPI, globs, activity, input_data):
    inp = copy.deepcopy(input_data) # Necessary, otherwise the function changes the values inside the dictionary -> need the original values for process trace
    func = globs[od.get_slot_value(activity, "func")]
    return func(inp) if func.__code__.co_argcount > 0 else func()


def handle_artefact(od: ODAPI, activity, artefact_type, relation_type, data_port=None, data=None,
                    direction="DataFlowIn"):
    artefact = od.create_object(None, "pt_Artefact")
    if 'pt_Consumes' == relation_type:
        od.create_link(None, relation_type, artefact, activity)
    else:
        od.create_link(None, relation_type, activity, artefact)
    if data_port:
        flow_direction = od.get_incoming if relation_type == 'pt_Consumes' else od.get_outgoing
        ass_side = od.get_source if relation_type == 'pt_Consumes' else od.get_target
        pm_artefact = ass_side(flow_direction(data_port, f"pm_{direction}")[0])
        prev_artefact = find_previous_artefact(od, od.get_incoming(pm_artefact, "pt_BelongsTo"))
        if prev_artefact:
            od.create_link(None, "pt_PrevVersion", artefact, prev_artefact)
        od.create_link(None, "pt_BelongsTo", artefact, pm_artefact)
        if data is not None:
            artefact_state = od.get_source(od.get_incoming(pm_artefact, "pm_Of")[0])
            od.set_slot_value(artefact_state, "data", serialize(data))
            od.set_slot_value(artefact, "data", serialize(data))


def find_previous_artefact(od: ODAPI, linked_artefacts):
    return next((od.get_source(link) for link in linked_artefacts if
                 not od.get_incoming(od.get_source(link), "pt_PrevVersion")), None)


def update_control_states(od: ODAPI, activity, ctrl_out):
    for has_ctrl_in in od.get_outgoing(activity, "pm_HasCtrlIn"):
        od.set_slot_value(od.get_source(od.get_incoming(od.get_target(has_ctrl_in), "pm_Of")[0]), "active", False)
    od.set_slot_value(od.get_source(od.get_incoming(ctrl_out, "pm_Of")[0]), "active", True)
