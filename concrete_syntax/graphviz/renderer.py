import functools
from uuid import UUID
from services import scd, od
from services.bottom.V0 import Bottom
from concrete_syntax.common import display_value, display_name, indent

# Turn ModelVerse/muMLE ID into GraphViz ID
def make_graphviz_id(uuid, prefix="") -> str:
    result = 'n'+(prefix+str(uuid).replace('-',''))[24:] # we assume that the first 24 characters are always zero...
    return result

# Parameter 'reify': If true, will create a node in the middle of every link. This allows links to be the src/tgt of other links (which muMLE supports), at the cost of a larger diagram.
# Parameter 'only_render': if specified, only render instances of these types. E.g., ["Place", "connection"]
# Parameter 'type_to_style': mapping from type-name to graphviz style. E.g., { "generic_link": ",color=purple" }
def render_object_diagram(state, m, mm, render_attributes=True, prefix_ids="", reify=False, only_render=None, type_to_style={}):
    bottom = Bottom(state)
    mm_scd = scd.SCD(mm, state)
    m_od = od.OD(mm, m, state)

    make_id = functools.partial(make_graphviz_id, prefix=prefix_ids)

    output = ""

    # Render objects
    for class_name, class_node in mm_scd.get_classes().items():
        if only_render != None and class_name not in only_render:
            continue

        output += f"\nsubgraph {class_name} {{"

        if render_attributes:
            attributes = od.get_attributes(bottom, class_node)


        custom_style = type_to_style.get(class_name, "")
        if custom_style == "":
            output += f"\nnode [shape=rect]"
        else:
            output += f"\nnode [shape=rect,{custom_style}]"

        for obj_name, obj_node in m_od.get_objects(class_node).items():
            output += f"\n{make_id(obj_node)} [label=\"{display_name(obj_name)} : {class_name}\"] ;"
            #" {{"

            # if render_attributes:
            #     for attr_name, attr_edge in attributes:
            #         slot = m_od.get_slot(obj_node, attr_name)
            #         if slot != None:
            #             val, type_name = od.read_primitive_value(bottom, slot, mm)
            #             output += f"\n{attr_name} => {display_value(val, type_name)}"
            # output += '\n}'

        output += '\n}'

    output += '\n'

    # Render links
    for assoc_name, assoc_edge in mm_scd.get_associations().items():
        if only_render != None and assoc_name not in only_render:
            continue

        output += f"\nsubgraph {assoc_name} {{"

        custom_style = type_to_style.get(assoc_name, "")
        if custom_style != "":
            output += f"\nedge [{custom_style}]"
        if reify:
            if custom_style != "":
                # created nodes will be points of matching style:
                output += f"\nnode [{custom_style},shape=point]"
            else:
                output += "\nnode [shape=point]"

        for link_name, link_edge in m_od.get_objects(assoc_edge).items():
            src_obj = bottom.read_edge_source(link_edge)
            tgt_obj = bottom.read_edge_target(link_edge)
            src_name = m_od.get_object_name(src_obj)
            tgt_name = m_od.get_object_name(tgt_obj)

            if reify:
                # intermediary node:
                output += f"\n{make_id(src_obj)} -> {make_id(link_edge)} [arrowhead=none]"
                output += f"\n{make_id(link_edge)} -> {make_id(tgt_obj)}"
                output += f"\n{make_id(link_edge)} [xlabel=\"{display_name(link_name)} : {assoc_name}\"]"
            else:
                output += f"\n{make_id(src_obj)} -> {make_id(tgt_obj)} [label=\"{display_name(link_name)}:{assoc_name}\", {custom_style}] ;"

        output += '\n}'

    return output

def render_trace_match(state, name_mapping: dict, pattern_m: UUID, host_m: UUID, color="grey", prefix_pattern_ids="", prefix_host_ids=""):
    bottom = Bottom(state)
    class_type = od.get_scd_mm_class_node(bottom)
    attr_link_type = od.get_scd_mm_attributelink_node(bottom)

    make_pattern_id = functools.partial(make_graphviz_id, prefix=prefix_pattern_ids)
    make_host_id = functools.partial(make_graphviz_id, prefix=prefix_host_ids)

    output = ""

    # render_suffix = f"#line:{color};line.dotted;text:{color} : matchedWith"
    render_suffix = f"[label=\"\",style=dashed,color={color}] ;"

    for pattern_el_name, host_el_name in name_mapping.items():
        # print(pattern_el_name, host_el_name)
        try:
            pattern_el, = bottom.read_outgoing_elements(pattern_m, pattern_el_name)
            host_el, = bottom.read_outgoing_elements(host_m, host_el_name)
        except:
            continue
        # only render 'match'-edges between objects (= those elements where the type of the type is 'Class'):
        pattern_el_type = od.get_type(bottom, pattern_el)
        pattern_el_type_type = od.get_type(bottom, pattern_el_type)
        if pattern_el_type_type == class_type:
            output += f"\n{make_pattern_id(pattern_el)} -> {make_host_id(host_el)} {render_suffix}"
        # elif pattern_el_type_type == attr_link_type:
        #     pattern_obj = bottom.read_edge_source(pattern_el)
        #     pattern_attr_name = od.get_attr_name(bottom, pattern_el_type)
        #     host_obj = bottom.read_edge_source(host_el)
        #     host_el_type = od.get_type(bottom, host_el)
        #     host_attr_name = od.get_attr_name(bottom, host_el_type)
        #     output += f"\n{make_pattern_id(pattern_obj)}::{pattern_attr_name} -> {make_host_id(host_obj)}::{host_attr_name} {render_suffix}"
    return output

def render_package(name, contents):
    output = f"subgraph cluster_{name} {{\n  label=\"{name}\";"
    output += indent(contents, 2)
    output += "\n}\n"
    return output
