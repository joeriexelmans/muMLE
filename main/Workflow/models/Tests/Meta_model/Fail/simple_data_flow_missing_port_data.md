a1:Place {
    Name="a";
	Process = "d_out";
    Sync = False;
	Start = True;
}
a2:Place {
    Name="a";
	Process = "d_through";
    Sync = False;
	Start = False;
}
a1flow_out1:Port {
	Name = "out";
}
a1data_out1:Port {
	Name = "id";
}
a2flow_in1:Port {
	Name = "in";
}
a2data_in1:Port {
	Name = "id";
}
rt_state:RTState {
}

:Transition (a1flow_out1 -> a2flow_in1) {
}
:Data_flow (a1data_out1 -> a2data_in1) {
}
:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_out (a1 -> a1flow_out1) {
}
:Port_data_in (a2 -> a2data_in1) {
}
:Port_data_out (a1 -> a1data_out1) {
}
:Running (rt_state -> a1) {
	Id="";
}