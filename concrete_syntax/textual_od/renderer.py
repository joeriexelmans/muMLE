# Renderer for Object Diagrams textual concrete syntax

from services import od
from services.bottom.V0 import Bottom
import json

def display_value(val: any):
    if isinstance(val, str):
        return '"'+val+'"'
    elif isinstance(val, int) or isinstance(val, bool):
        return str(val)
    else:
        raise Exception("don't know how to display value" + str(val))

def render_od(state, m_id, mm_id, hide_names=True):
    bottom = Bottom(state)
    output = ""
    
    m_od = od.OD(mm_id, m_id, state)

    def display_name(name: str):
        # object names that start with "__" are hidden
        return name if (name[0:2] != "__" or not hide_names) else ""

    def write_attributes(object_node):
        o = ""
        for attr_name, slot_node in m_od.get_slots(object_node):
            value = m_od.read_slot(slot_node)
            o += f"    {attr_name} = {display_value(value)}\n"
        return o

    for class_name, objects in m_od.get_all_objects().items():
        for object_name, object_node in objects.items():
            output += f"{display_name(object_name)}:{class_name}\n"
            output += write_attributes(object_node)

    for assoc_name, links in m_od.get_all_links().items():
        for link_name, (link_edge, src_name, tgt_name) in links.items():
            output += f"{display_name(link_name)}:{assoc_name} ({src_name} -> {tgt_name})\n"
            # links can also have slots:
            output += write_attributes(link_edge)

    return output