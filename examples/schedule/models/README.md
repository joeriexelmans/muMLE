
### association Exec_con
    Integer gate_from;
    Integer gate_to;

### association Data_con

### class Start [1..1]
### class End [1..*]


### class Match
    optional Integer n;

### class Rewrite

### class Data_modify
    String modify_dict;

### class Loop
    optional Boolean choise;

## debugging tools

### class Print(In_Exec, Out_Exec, In_Data)
    optional Boolean event;