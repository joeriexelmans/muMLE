from api.od import ODAPI
from concrete_syntax.graphviz.make_url import show_graphviz
from concrete_syntax.graphviz.renderer import make_graphviz_id

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

def render_petri_net_to_dot(od: ODAPI) -> str:
    dot = ""
    dot += "rankdir=LR;"
    dot += "center=true;"
    dot += "margin=1;"
    dot += "nodesep=1;"
    dot += "subgraph places {"
    dot += "  node [fontname=Arial,fontsize=10,shape=circle,fixedsize=true,label=\"\", height=.35,width=.35];"
    for place_name, place in od.get_all_instances("PNPlace"):
        # place_name = od.get_name(place)
        try:
            place_state = od.get_source(od.get_incoming(place, "pn_of")[0])
            num_tokens = od.get_slot_value(place_state, "numTokens")
        except IndexError:
            num_tokens = 0
        dot += f"  {make_graphviz_id(place)} [label=\"{place_name}\\n\\n{render_tokens(num_tokens)}\\n\\n­\"];\n"
    dot += "}\n"
    dot += "subgraph transitions {\n"
    dot += "  edge [arrowhead=normal];\n"
    dot += "  node [fontname=Arial,fontsize=10,shape=rect,fixedsize=true,height=.3,width=.12,style=filled,fillcolor=black,color=white];\n"
    for transition_name, transition in od.get_all_instances("PNTransition"):
        dot += f"  {make_graphviz_id(transition)} [label=\"{transition_name}\\n\\n\\n­\"];\n"
    dot += "}\n"
    for _, arc in od.get_all_instances("arc"):
        src = od.get_source(arc)
        tgt = od.get_target(arc)
        # src_name = od.get_name(od.get_source(arc))
        # tgt_name = od.get_name(od.get_target(arc))
        dot += f"{make_graphviz_id(src)} -> {make_graphviz_id(tgt)};"
    for _, inhib_arc in od.get_all_instances("inh_arc"):
        src = od.get_source(inhib_arc)
        tgt = od.get_target(inhib_arc)
        dot += f"{make_graphviz_id(src)} -> {make_graphviz_id(tgt)} [arrowhead=odot];\n"
    return dot

# deprecated
def render_petri_net(od: ODAPI, engine="neato"):
    show_graphviz(render_petri_net_to_dot(od), engine=engine)

# use this instead:
def show_petri_net(od: ODAPI, engine="neato"):
    show_graphviz(render_petri_net_to_dot(od), engine=engine)