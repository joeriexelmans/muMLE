p1:Place {
    Name="a";
    Process = "a1";
    Sync = False;
}
o1:Port {
    Name="out";
}
:Port_link_out (p1 -> o1)
d1:Port_data{
    value="";
}
:Port_data_connect (d1 -> o1)

o2:Port {
    Name="out2";
}
:Port_link_out (p1 -> o2)
d2:Port_data{
    value="";
}
:Port_data_connect (d2 -> o2)

p2:Place {
    Name="a";
    Process = "a2";
    Sync = False;
}
i1:Port {
    Name="in";
}

:Port_link_in (p2 -> i1)

:Transition (p1->p2)
:Data_flow (o1 -> i1)

rt_state:RTState
:Running (rt_state -> p1){
    Id='';
}
:RT_data_connect (rt_state -> d1)
:RT_data_connect (rt_state -> d2)