# Renderer for Object Diagrams textual concrete syntax

from services import od
from concrete_syntax.common import display_value


def render_od(state, m_id, mm_id, hide_names=True):
    output = ""
    
    m_od = od.OD(mm_id, m_id, state)

    serialized = set(["Integer", "String", "Boolean", "ActionCode", "Bytes"]) # assume these types always already exist

    def display_name(name: str):
        # object names that start with "__" are hidden
        return name if (name[0:2] != "__" or not hide_names) else ""

    def write_attributes(object_node):
        o = ""
        slots = m_od.get_slots(object_node)
        if len(slots) > 0:
            o += " {"
            for attr_name, slot_node in slots:
                value, type_name = m_od.read_slot(slot_node)
                o += f"\n    {attr_name} = {display_value(value, type_name, indentation=4)};"
            o += "\n}"
        return o

    for class_name, objects in m_od.get_all_objects().items():
        for object_name, object_node in objects.items():
            if class_name == "ModelRef":
                continue # skip modelrefs, they fuckin ma shit up
            output += f"\n{display_name(object_name)}:{class_name}"
            output += write_attributes(object_node)
            serialized.add(object_name)

    todo_links = m_od.get_all_links()

    while len(todo_links) != 0:
        postponed = {}
        for assoc_name, links in todo_links.items():
            for link_name, (link_edge, src_name, tgt_name) in links.items():
                if link_name in serialized:
                    continue
                if src_name not in serialized or tgt_name not in serialized:
                    postponed[assoc_name] = links
                    break
                output += f"\n{display_name(link_name)}:{assoc_name} ({src_name} -> {tgt_name})"
                # links can also have slots:
                output += write_attributes(link_edge)
                serialized.add(link_name)
        if len(postponed) == len(todo_links):
            raise Exception(f"We got stuck! Links = {postponed}")
        todo_links = postponed

    return output