p1:Place{start = True;}
p2:Place
p3:Place
p4:Place{start = True;}

:Transition (p1->p2)
:Transition (p2->p1)
:Transition (p2->p3)
:Transition (p3->p2)
:Transition (p3->p4)
:Transition (p4->p3)
:Transition (p4->p1)
:Transition (p1->p4)

rt_state:RTState
:Running (rt_state -> p1)
:Running (rt_state -> p4)

