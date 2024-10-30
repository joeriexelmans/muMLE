import urllib
from concrete_syntax.common import indent
from examples.semantics.operational.port.helpers import design_to_state, state_to_design, get_time, get_num_ships

def render_port_graphviz(od):
    txt = ""

    def render_place(place):
        name = od.get_name(place)
        return f'"{name}" [ label = "{name}\\n ships = {get_num_ships(od, place)}", style = filled, fillcolor = lightblue ]\n'

    for _, cap in od.get_all_instances("CapacityConstraint", include_subtypes=False):
        name = od.get_name(cap)
        capacity = od.get_slot_value(cap, "shipCapacity")
        txt += f'subgraph cluster_{name} {{\n  label = "{name}\\n capacity = {capacity}";\n'
        for lnk in od.get_outgoing(cap, "capacityOf"):
            place = od.get_target(lnk)
            txt += f'  {render_place(place)}'
        txt += f'}}\n'

    for _, place_state in od.get_all_instances("PlaceState", include_subtypes=False):
        place = state_to_design(od, place_state)
        if len(od.get_incoming(place, "capacityOf")) == 0:
            txt += render_place(place)

    for _, berth_state in od.get_all_instances("BerthState", include_subtypes=False):
        berth = state_to_design(od, berth_state)
        name = od.get_name(berth)
        txt += f'"{name}" [ label = "{name}\\n numShips = {get_num_ships(od, berth)}\\n status = {od.get_slot_value(berth_state, "status")}", fillcolor = yellow, style = filled]\n'

    for _, gen in od.get_all_instances("Generator", include_subtypes=False):
        txt += f'"{od.get_name(gen)}" [ label = "+", shape = diamond, fillcolor = green, fontsize = 30, style = filled ]\n'

    for _, conn in od.get_all_instances("connection"):
        src = od.get_source(conn)
        tgt = od.get_target(conn)
        moved = od.get_slot_value(design_to_state(od, conn), "moved")
        src_name = od.get_name(src)
        tgt_name = od.get_name(tgt)
        txt += f"{src_name} -> {tgt_name} [color=deepskyblue3, penwidth={1 if moved else 2}];\n"

    for _, workers in od.get_all_instances("WorkerSet"):
        already_have = []
        name = od.get_name(workers)
        num_workers = od.get_slot_value(workers, "numWorkers")
        txt += f'{name} [label="{num_workers} worker(s)", shape=parallelogram, fillcolor=chocolate, style=filled];\n'
        for lnk in od.get_outgoing(design_to_state(od, workers), "isOperating"):
            berth = od.get_target(lnk)
            already_have.append(berth)
            txt += f"{name} -> {od.get_name(berth)} [arrowhead=none, color=chocolate];\n"
        for lnk in od.get_outgoing(workers, "canOperate"):
            berth = od.get_target(lnk)
            if berth not in already_have:
                txt += f"{name} -> {od.get_name(berth)} [style=dotted, arrowhead=none, color=chocolate];\n"

    graphviz = f"digraph {{\n{indent(txt, 2)}}}"

    return "https://dreampuf.github.io/GraphvizOnline/#"+urllib.parse.quote(graphviz)

def render_port_textual(od):
    txt = ""
    for _, place_state in od.get_all_instances("PlaceState", include_subtypes=False):
        place = state_to_design(od, place_state)
        name = od.get_name(place)
        txt += f'place "{name}" {"🚢"*get_num_ships(od, place)}\n'

    for _, berth_state in od.get_all_instances("BerthState", include_subtypes=False):
        berth = state_to_design(od, berth_state)
        name = od.get_name(berth)
        txt += f'berth "{name}" {"🚢"*get_num_ships(od, berth)} {od.get_slot_value(berth_state, "status")}\n'

    return txt
