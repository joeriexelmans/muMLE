a1:Place {
    Name="a";
	Process = "a";
    Sync = False;
	Start = False;
}
a2:Place {
    Name="a";
	Process = "activity_ref";
    Sync = False;
	Start = False;
}
a1flow_out1:Port {
	Name = "new_port_1";
}
a2flow_in1:Port {
	Name = "inputFlow";
}
rt_state:RTState {
}


:Transition (a1flow_out1 -> a2flow_in1) {
}

:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_out (a1 -> a1flow_out1) {
}