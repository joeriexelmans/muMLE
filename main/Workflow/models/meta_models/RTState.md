abstract class Versioned
association Prev [0..*] Versioned -> Versioned [0..1]


class RTState [1..*] (Versioned) 

association Running [0..*] RTState -> Place [0..*] {
    String Id;
}

association Running_token [0..*] RTState -> Port [0..*]

class Port_data (Versioned) {
    ActionCode Value;
}
association Port_data_connect [0..*] Port_data -> Port [0..*]
association RT_data_connect [1..*] RTState -> Port_data [0..*]

global Port_data_constraint ```
    errors = []
    for (_, data_port_out) in get_all_instances("Port_data_out"):
        Port = get_target(data_port_out)
        if len(get_incoming(get_target(data_port_out), "Port_data_connect")) == 0:
            errors.append(f"Place '{get_name(get_source(data_port_out))}' Port '{get_slot_value(Port, "Name")}' does not have a Port_data connected")
    errors
```