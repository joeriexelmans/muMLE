process = ...

def _create_new_rt_state(rt_state) -> str:
    with process._bootstrap_lock:
        newRTModel = process.rule_executor.rewrite_rule(
            process.od, process.rules["create_new_RTState"], pivot={"rt_state_old": rt_state}
        ).__next__()["rt_state"]
        return {"flow": ["out"], "data": {"new_rt_state": newRTModel}}

def _copy_running(old_rt_state, new_rt_state, finished_task):
    with process._bootstrap_lock:
        process_running = None
        running_places = process.rule_executor.match_rule(
            process.od, process.rules["get_running"], pivot={"state": old_rt_state}
        )
        for run in running_places:
            m = process.rule_executor.rewrite_rule(
                process.od,
                process.rules["copy_running"],
                pivot={
                    "p_running": run["p_running"],
                    "run.Id": run["run.Id"],
                    "state": new_rt_state,
                },
            ).__next__()
            if process.od.get_value(process.od.get(m["run.Id"])) == finished_task:
                process_running = m
                process_running.pop("run.Id")

        # process.rule_executor.rewrite_rule(
        #     process.od, process.rules["delete_running"], pivot=process_running
        # ).__next__()

        return {"flow": ["out"], "data": {"activity_finished": process_running["p_running"]}}

def _copy_running_tokens(old_rt_state, new_rt_state):
    with process._bootstrap_lock:
        tokens = process.rule_executor.match_rule(process.od, process.rules["get_running_token"], pivot={"state": old_rt_state})
        [process.rule_executor.rewrite_rule(process.od, process.rules["get_running_token"],
                                         pivot={"state": new_rt_state, "port_running": token["port_running"]}).__next__() for
         token in tokens]
        return {"flow": ["out"], "data": {}}

def _update_data(old_rt_state, new_rt_state, results, activity):
    with process._bootstrap_lock:
        process._copy_data(old_rt_state, new_rt_state)
        data_ports = process.rule_executor.match_rule(
            process.od, process.rules["get_data"], pivot={"state": new_rt_state, "place": activity}
        )
        for data_port in data_ports:
            port_name = process.od.get_slot_value(process.od.get(data_port["port"]), "Name")
            m = process.rule_executor.rewrite_rule(
                process.od,
                process.rules["create_data"],
                pivot=data_port,
            ).__next__()
            value = results.get(port_name, None)
            value = f"'{value}'" if type(value) == str else value.__str__()
            process.od.set_slot_value(process.od.get(m["new_data"]), "Value", value)
        return {"flow": ["out"], "data": {}}
    
def _get_next_activities(activity_finished, new_rt_state, flow_output):
    running_places = [
        state["p_next"]
        for state in process.rule_executor.match_rule(
            process.od,
            process.rules["action_next_states"],
            pivot={"p_running": activity_finished},
            params={"port_names": flow_output, "sync": False},
        )
    ]
    running_places_sync = [
        state
        for state in process.rule_executor.match_rule(
            process.od,
            process.rules["action_next_states"],
            pivot={"p_running": activity_finished},
            params={"port_names": flow_output, "sync": True},
        )
    ]
    [
        process.rule_executor.rewrite_rule(
            process.od,
            process.rules["create_running_token"],
            pivot={**match, "state": new_rt_state},
            params={"sync": True},
        ).__next__()
        for match in running_places_sync
    ]
    for place in running_places_sync:
        sufficient_tokens = True
        tokens = []
        for port in process.rule_executor.match_rule(process.od, process.rules["get_flow_input_port"],
                                                  pivot={"place": place["p_next"]}):
            matches = [i for i in process.rule_executor.match_rule(process.od, process.rules["get_flow_token"],
                                                                pivot={**port, "state": new_rt_state})]
            if len(matches) == 0:
                sufficient_tokens = False
                break
            tokens.append(matches[0]["token"])
        if sufficient_tokens:
            process.rule_executor.rewrite_rule(process.od, process.rules["delete"],
                                            pivot={f"_{i}": t for i, t in enumerate(tokens)}).__next__()
            running_places.append(place["p_next"])
    return {"flow": ["out"], "data": {"new_activities": running_places}}

def _create_activities_data(new_rt_state, new_activities):
    data = process._create_running_places(
            new_rt_state, new_activities
        )
    return {"flow": [], "data": {"data": data}}