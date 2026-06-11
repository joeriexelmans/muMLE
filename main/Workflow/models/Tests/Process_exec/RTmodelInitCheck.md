a1:Place {
	Name = "init";
	Process = "init_check";
	Start = True;
	Sync = False;
}
a1data_in1:Port {
	Name = "inp";
}
a1data_out1:Port {
	Name = "out";
}
rt_state:RTState {
}
d1data_out1:Port_data {
	Value = "None";
}


:Data_flow (a1data_out1 -> a1data_in1) {
}


:Port_data_in (a1 -> a1data_in1) {
}
:Port_data_out (a1 -> a1data_out1) {
}
:Running (rt_state -> a1) {
	Id="";
}
:RT_data_connect (rt_state -> d1data_out1) {
}
:Port_data_connect (d1data_out1 -> a1data_out1) {
}