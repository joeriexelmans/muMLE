class Place {
    String Name;
    String Process;
    Boolean Sync;
    optional Boolean Start;
}

class Port {
    String Name;
    ```
    result = True
    if (sum([len(get_incoming(this, tp)) for tp in ["Port_data_in", "Port_data_out", "Port_flow_in", "Port_flow_out"]]) != 1):
        result = "Port must be connected as an input or output"
    result
    ```;
}

association Port_data_in [0..1] Place -> Port [0..*]
association Port_data_out [0..1] Place -> Port [0..*]
association Port_flow_in [0..1] Place -> Port [0..*]
association Port_flow_out [0..1] Place -> Port [0..*]


association Transition [0..*] Port -> Port [0..*]
association Data_flow [0..*] Port -> Port [0..*]