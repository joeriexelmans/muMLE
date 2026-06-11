a1:Place {
    Name="a";
	Process = "a1";
	Start = True;
	Sync = False;
}
a2:Place {
    Name="a";
	Process = "a2";
	Start = False;
	Sync = False;
}
a3:Place {
    Name="a";
	Process = "a3";
	Start = False;
	Sync = False;
}
a4:Place {
    Name="a";
	Process = "a4";
	Start = False;
	Sync = True;
}
a1flow_in1:Port {
	Name = "in";
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
a3flow_out1:Port {
	Name = "out";
}
a4flow_in1:Port {
	Name = "in";
}
a4flow_in2:Port {
	Name = "in";
}
a4flow_out1:Port {
	Name = "out";
}
rt_state:RTState {
}


:Transition (a1flow_out1 -> a2flow_in1) {
}
:Transition (a1flow_out1 -> a3flow_in1) {
}
:Transition (a2flow_out1 -> a4flow_in2) {
}
:Transition (a4flow_out1 -> a1flow_in1) {
}
:Transition (a3flow_out1 -> a4flow_in1) {
}

:Port_flow_in (a1 -> a1flow_in1) {
}
:Port_flow_in (a2 -> a2flow_in1) {
}
:Port_flow_in (a3 -> a3flow_in1) {
}
:Port_flow_in (a4 -> a4flow_in1) {
}
:Port_flow_in (a4 -> a4flow_in2) {
}
:Port_flow_out (a1 -> a1flow_out1) {
}
:Port_flow_out (a2 -> a2flow_out1) {
}
:Port_flow_out (a3 -> a3flow_out1) {
}
:Port_flow_out (a4 -> a4flow_out1) {
}


:Running (rt_state -> a1) {
	Id="";
}