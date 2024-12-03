from api.od import ODAPI
from concrete_syntax.graphviz.make_url import show_graphviz

try:
    import graphviz
    HAVE_GRAPHVIZ = True
except ImportError:
    HAVE_GRAPHVIZ = False

def render_tokens(num_tokens: int):
    if 0 <= num_tokens <= 3:
        return '●'*num_tokens
    if num_tokens == 4:
        return '●●\\n●●'
    return str(num_tokens)

def render_petri_net(od: ODAPI):
    dot = ""
    dot += "rankdir=LR;"
    dot += "center=true;"
    dot += "margin=1;"
    dot += "nodesep=1;"
    dot += "edge [arrowhead=vee];"
    dot += "node[fontname=Arial,fontsize=10];\n"
    dot += "subgraph places {"
    dot += "  node [shape=circle,fixedsize=true,label=\"\", height=.35,width=.35];"
    for _, place_state in od.get_all_instances("PNPlaceState"):
        place = od.get_target(od.get_outgoing(place_state, "pn_of")[0])
        place_name = od.get_name(place)
        num_tokens = od.get_slot_value(place_state, "numTokens")
        dot += f"  {place_name} [label=\"{place_name}\\n\\n{render_tokens(num_tokens)}\\n\\n­\"];\n"
    dot += "}\n"
    dot += "subgraph transitions {"
    dot += "  node [shape=rect,fixedsize=true,height=.3,width=.12,style=filled,fillcolor=black,color=white];\n"
    for transition_name, _ in od.get_all_instances("PNTransition"):
        dot += f"  {transition_name} [label=\"{transition_name}\\n\\n\\n­\"];\n"
    dot += "}\n"
    for _, arc in od.get_all_instances("arc"):
        src_name = od.get_name(od.get_source(arc))
        tgt_name = od.get_name(od.get_target(arc))
        dot += f"{src_name} -> {tgt_name};"
    show_graphviz(dot, engine="dot")
    return ""
