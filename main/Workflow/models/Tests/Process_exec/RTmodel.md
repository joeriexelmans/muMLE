p1:Place {
    Name="a";
    Process = "f1";
    Sync = False;
}

p2:Place {
    Name="a";
    Process = "f2";
    Sync = False;
}

:Transition (p1 -> p2)
:Transition (p2 -> p1)

rt_state:RTState
:Running (rt_state -> p1){
    Id='';
}
