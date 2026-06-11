a1:Place {
	Name = "activity 1";
	Process = "a1";
	Start = True;
	Sync = False;
}
a2:Place {
	Name = "activity 2";
	Process = "a2";
	Start = False;
	Sync = True;
}
a3:Place {
	Name = "activity 3";
	Process = "a3";
	Start = False;
	Sync = False;
}
a1flow_out1:Port {
	Name = "out";
}
a2flow_in1:Port {
	Name = "in";
}
a2flow_out1:Port {
	Name = "out";
}
a3flow_in1:Port {
	Name = "in";
}
a3data_out1:Port {
	Name = "new_port_1";
}
rt_state:RTState {
}
d3data_out1:Port_data {
	Value = "None";
}

:Transition (a1flow_out1 -> a2flow_in1) {
}
:Transition (a2flow_out1 -> a3flow_in1) {
}

:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_in (a3 -> a3flow_in1) {
}
:Port_flow_out (a1 -> a1flow_out1) {
}
:Port_flow_out (a2 -> a2flow_out1) {
}

:Port_data_out (a3 -> a3data_out1) {
}
:Running (rt_state -> a1) {
	Id="";
}
:RT_data_connect (rt_state -> d3data_out1) {
}
:Port_data_connect (d3data_out1 -> a3data_out1) {
}