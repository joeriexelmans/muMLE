from api.od import ODAPI
from concrete_syntax.graphviz.make_url import make_url

def render_petri_net(od: ODAPI):
    dot = ""
    dot += "rankdir=LR;"
    dot += "center=true;"
    dot += "margin=1;"
    dot += "nodesep=1;"
    dot += "edge [arrowhead=vee];"
    dot += "node[fontname=Arial,fontsize=10];\n"
    dot += "subgraph places {"
    dot += "  node [shape=circle,fixedsize=true,label=\"\", height=.3,width=.3];"
    for _, place_state in od.get_all_instances("PlaceState"):
        place = od.get_target(od.get_outgoing(place_state, "of")[0])
        place_name = od.get_name(place)
        num_tokens = od.get_slot_value(place_state, "numTokens")
        dot += f"  {place_name} [label=\"{place_name}\\n\\n{'●'*num_tokens}\\n\\n­\"];\n"
    dot += "}\n"
    dot += "subgraph transitions {"
    dot += "  node [shape=rect,fixedsize=true,height=.4,width=.15,style=filled,fillcolor=black,color=white];\n"
    for transition_name, _ in od.get_all_instances("Transition"):
        dot += f"  {transition_name} [label=\"{transition_name}\\n\\n\\n\\n­\"];\n"
    dot += "}\n"
    for _, arc in od.get_all_instances("arc"):
        src_name = od.get_name(od.get_source(arc))
        tgt_name = od.get_name(od.get_target(arc))
        dot += f"{src_name} -> {tgt_name};"
    return make_url(dot, engine="circo")
