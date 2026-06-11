a1:Place {
    Name="a";
	Process = "choiseR";
	Start = True;
	Sync = False;
}
a2:Place {
    Name="a";
	Process = "rec1";
	Start = False;
	Sync = False;
}
a3:Place {
    Name="a";
	Process = "a1";
	Start = False;
	Sync = False;
}
a1flow_out1:Port {
	Name = "out1";
}
a1flow_out2:Port {
	Name = "out2";
}
a2flow_in1:Port {
	Name = "inputFlow";
}
a3flow_in1:Port {
	Name = "inputFlow";
}
rt_state:RTState {
}


:Transition (a1flow_out1 -> a3flow_in1) {
}
:Transition (a1flow_out2 -> a2flow_in1) {
}

:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_in (a3 -> a3flow_in1) {
}
:Port_flow_out (a1 -> a1flow_out1) {
}
:Port_flow_out (a1 -> a1flow_out2) {
}


:Running (rt_state -> a1) {
	Id="";
}