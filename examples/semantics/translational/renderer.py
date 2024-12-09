from api.od import ODAPI
from concrete_syntax.graphviz.renderer import render_object_diagram, make_graphviz_id
from concrete_syntax.graphviz.make_url import show_graphviz
from examples.petrinet.renderer import render_petri_net_to_dot
from examples.semantics.operational.port.renderer import render_port_to_dot
from examples.semantics.operational.port import helpers

# COLORS
PLACE_BG = "#DAE8FC" # fill color
PLACE_FG = "#6C8EBF" # font, line, arrow
BERTH_BG = "#FFF2CC"
BERTH_FG = "#D6B656"
CAPACITY_BG = "#F5F5F5"
CAPACITY_FG = "#666666"
WORKER_BG = "#D5E8D4"
WORKER_FG = "#82B366"
GENERATOR_BG = "#FFE6CC"
GENERATOR_FG = "#D79B00"
CLOCK_BG = "black"
CLOCK_FG = "white"

def graphviz_style_fg_bg(fg, bg):
    return f"style=filled,fillcolor=\"{bg}\",color=\"{fg}\",fontcolor=\"{fg}\""

def render_port(state, m, mm):
    dot = render_object_diagram(state, m, mm,
        reify=True,
        only_render=[
            # Only render these types
            "Place", "Berth", "CapacityConstraint", "WorkerSet", "Generator", "Clock",
            "connection", "capacityOf", "canOperate", "generic_link",
            # Petri Net types not included (they are already rendered by other function)
            # Port-State-types not included to avoid cluttering the diagram, but if you need them, feel free to add them.
        ],
        # We can style nodes/edges according to their type:
        type_to_style={
            "Place": graphviz_style_fg_bg(PLACE_FG, PLACE_BG),
            "Berth": graphviz_style_fg_bg(BERTH_FG, BERTH_BG),
            "CapacityConstraint": graphviz_style_fg_bg(CAPACITY_FG, CAPACITY_BG),
            "WorkerSet": "shape=oval,"+graphviz_style_fg_bg(WORKER_FG, WORKER_BG),
            "Generator": "shape=parallelogram,"+graphviz_style_fg_bg(GENERATOR_FG, GENERATOR_BG),
            "Clock": graphviz_style_fg_bg(CLOCK_FG, CLOCK_BG),

            # same blue as Place, thick line:
            "connection": f"color=\"{PLACE_FG}\",fontcolor=\"{PLACE_FG}\",penwidth=2.0",

            # same grey as CapacityConstraint
            "capacityOf": f"color=\"{CAPACITY_FG}\",fontcolor=\"{CAPACITY_FG}\"",

            # same green as WorkerSet
            "canOperate": f"color=\"{WORKER_FG}\",fontcolor=\"{WORKER_FG}\"",

            # purple line
            "generic_link": "color=purple,fontcolor=purple,arrowhead=onormal",
        },
        # We have control over the node/edge labels that are rendered:
        type_to_label={
            "CapacityConstraint": lambda capconstr_name, capconstr, odapi: f"{capconstr_name}\\nshipCapacity={odapi.get_slot_value(capconstr, "shipCapacity")}",

            "Place": lambda place_name, place, odapi: f"{place_name}\\nnumShips={helpers.get_num_ships(odapi, place)}",

            "Berth": lambda berth_name, berth, odapi: f"{berth_name}\\nnumShips={helpers.get_num_ships(odapi, berth)}\\nstatus={odapi.get_slot_value(helpers.design_to_state(odapi, berth), "status")}",

            "Clock": lambda _, clock, odapi: f"Clock\\ntime={odapi.get_slot_value(clock, "time")}",

            "connection": lambda conn_name, conn, odapi: f"{conn_name}\\nmoved={odapi.get_slot_value(helpers.design_to_state(odapi, conn), "moved")}",

            # hide generic link labels
            "generic_link": lambda lnk_name, lnk, odapi: "",

            "WorkerSet": lambda ws_name, ws, odapi: f"{ws_name}\\nnumWorkers={odapi.get_slot_value(ws, "numWorkers")}",

            # hide the type (it's already clear enough)
            "Generator": lambda gen_name, gen, odapi: gen_name,
        },
    )
    return dot

def render_port_and_petri_net(state, m, mm):
    od = ODAPI(state, m, mm)
    dot = ""
    dot += "// petri net:\n"
    dot += render_petri_net_to_dot(od)
    dot += "\n// the rest:\n"
    dot += render_port(state, m, mm)
    return dot


def show_port_and_petri_net(state, m, mm, engine="dot"):
    show_graphviz(render_port_and_petri_net(state, m, mm), engine=engine)
