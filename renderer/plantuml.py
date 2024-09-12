from services import scd, od
from services.bottom.V0 import Bottom
from transformation import ramify
import json

def render_class_diagram(state, model):
    bottom = Bottom(state)
    model_scd = scd.SCD(model, state)
    model_od = od.OD(od.get_scd_mm(bottom), model, state)

    output = ""

    # Render classes
    for name, class_node in model_scd.get_classes().items():
        is_abstract = False
        slot = model_od.get_slot(class_node, "abstract")
        if slot != None:
            is_abstract = od.read_primitive_value(bottom, slot, model_od.type_model)

        if is_abstract:
            output += f"\nabstract class \"{name}\" as {make_id(class_node)}"
        else:
            output += f"\nclass \"{name}\" as {make_id(class_node)}"

        # Render attributes
        output += " {"
        for attr_name, attr_edge in od.get_attributes(bottom, class_node):
            tgt_name = model_scd.get_class_name(bottom.read_edge_target(attr_edge))
            output += f"\n  {attr_name} : {tgt_name}"
        output += "\n}"

    output += "\n"

    # Render inheritance links
    for inh_node in model_scd.get_inheritances().values():
        src_node = bottom.read_edge_source(inh_node)
        tgt_node = bottom.read_edge_target(inh_node)
        output += f"\n{make_id(tgt_node)} <|-- {make_id(src_node)}"

    output += "\n"

    # Render associations
    for assoc_name, assoc_edge in model_scd.get_associations().items():
        src_node = bottom.read_edge_source(assoc_edge)
        tgt_node = bottom.read_edge_target(assoc_edge)

        src_lower_card, src_upper_card, tgt_lower_card, tgt_upper_card = model_scd.get_assoc_cardinalities(assoc_edge)

        # default cardinalities
        if src_lower_card == None:
            src_lower_card = 0
        if src_upper_card == None:
            src_upper_card = "*"
        if tgt_lower_card == None:
            tgt_lower_card = 0
        if tgt_upper_card == None:
            tgt_upper_card = "*"

        src_card = f"{src_lower_card} .. {src_upper_card}"
        tgt_card = f"{tgt_lower_card} .. {tgt_upper_card}"

        if src_card == "0 .. *":
            src_card = " " # hide cardinality
        if tgt_card == "1 .. 1":
            tgt_card = " " # hide cardinality
        
        output += f'\n{make_id(src_node)} "{src_card}" --> "{tgt_card}" {make_id(tgt_node)} : {assoc_name}'

    return output


def render_object_diagram(state, m, mm, render_attributes=True):
    bottom = Bottom(state)
    mm_scd = scd.SCD(mm, state)
    m_od = od.OD(mm, m, state)

    output = ""

    # Render objects
    for class_name, class_node in mm_scd.get_classes().items():
        if render_attributes:
            attributes = od.get_attributes(bottom, class_node)

        for obj_name, obj_node in m_od.get_objects(class_node).items():
            output += f"\nmap \"{obj_name} : {class_name}\" as {make_id(obj_node)} {{"

            if render_attributes:
                for attr_name, attr_edge in attributes:
                    slot = m_od.get_slot(obj_node, attr_name)
                    if slot != None:
                        output += f"\n{attr_name} => {json.dumps(od.read_primitive_value(bottom, slot, mm))}"
            output += '\n}'

    output += '\n'

    # Render links
    for assoc_name, assoc_edge in mm_scd.get_associations().items():
        for link_name, link_edge in m_od.get_objects(assoc_edge).items():
            src_obj = bottom.read_edge_source(link_edge)
            tgt_obj = bottom.read_edge_target(link_edge)
            src_name = m_od.get_object_name(src_obj)
            tgt_name = m_od.get_object_name(tgt_obj)

            output += f"\n{make_id(src_obj)} -> {make_id(tgt_obj)} : {assoc_name}"

    return output

def render_package(name, contents):
    output = ""
    output += f'\npackage "{name}" {{'
    output += contents
    output += '\n}'
    return output

def render_trace_ramifies(state, mm, ramified_mm, render_attributes=True):
    bottom = Bottom(state)

    mm_scd = scd.SCD(mm, state)
    ramified_mm_scd = scd.SCD(ramified_mm, state)

    output = ""

    # Render RAMifies-edges between classes
    for ram_name, ram_class_node in ramified_mm_scd.get_classes().items():
        original_class, = bottom.read_outgoing_elements(ram_class_node, ramify.RAMIFIES_LABEL)
        original_name = mm_scd.get_class_name(original_class)
        output += f"\n{make_id(ram_class_node)} ..> {make_id(original_class)} #line:green;text:green : RAMifies"

        if render_attributes:
            # and between attributes
            for (ram_attr_name, ram_attr_edge) in od.get_attributes(bottom, ram_class_node):
                orig_attr_edge, = bottom.read_outgoing_elements(ram_attr_edge, ramify.RAMIFIES_LABEL)
                orig_class_node = bottom.read_edge_source(orig_attr_edge)
                # dirty AF:
                orig_attr_name = mm_scd.get_class_name(orig_attr_edge)[len(original_name)+1:]
                output += f"\n{make_id(ram_class_node)}::{ram_attr_name} ..> {make_id(orig_class_node)}::{orig_attr_name} #line:green;text:green : RAMifies"

    return output


def render_trace_conformance(state, m, mm, render_attributes=True):
    bottom = Bottom(state)
    mm_scd = scd.SCD(mm, state)
    m_od = od.OD(mm, m, state)

    output = ""

    # Render objects
    for class_name, class_node in mm_scd.get_classes().items():

        if render_attributes:
            attributes = od.get_attributes(bottom, class_node)

        for obj_name, obj_node in m_od.get_objects(class_node).items():
            output += f"\n{make_id(obj_node)} ..> {make_id(class_node)} #line:blue;text:blue : instanceOf"

            if render_attributes:
                for attr_name, attr_edge in attributes:
                    slot = m_od.get_slot(obj_node, attr_name)
                    if slot != None:
                        output += f"\n{make_id(obj_node)}::{attr_name} ..> {make_id(class_node)}::{attr_name} #line:blue;text:blue : instanceOf"

    output += '\n'

    return output

def render_trace_match(state, mapping):
    bottom = Bottom(state)
    class_type = od.get_scd_mm_class_node(bottom)
    attr_link_type = od.get_scd_mm_attributelink_node(bottom)

    output = ""

    for pattern_el, host_el in mapping.items():
        # only render 'match'-edges between objects (= those elements where the type of the type is 'Class'):
        pattern_el_type = od.get_type(bottom, pattern_el)
        pattern_el_type_type = od.get_type(bottom, pattern_el_type)
        if pattern_el_type_type == class_type:
            output += f"\n{make_id(pattern_el)} ..> {make_id(host_el)} #line:grey;text:grey : matchedWith"
        elif pattern_el_type_type == attr_link_type:
            pattern_obj = bottom.read_edge_source(pattern_el)
            pattern_attr_name = od.get_attr_name(bottom, pattern_el_type)
            host_obj = bottom.read_edge_source(host_el)
            host_el_type = od.get_type(bottom, host_el)
            host_attr_name = od.get_attr_name(bottom, host_el_type)
            output += f"\n{make_id(pattern_obj)}::{pattern_attr_name} ..> {make_id(host_obj)}::{host_attr_name} #line:grey;text:grey : matchedWith"
    return output

def make_id(uuid) -> str:
    return (str(uuid).replace('-','_'))