from services import scd, od
from services.bottom.V0 import Bottom
from transformation import ramify

def render_class_diagram(state, model):
    bottom = Bottom(state)
    model_scd = scd.SCD(model, state)
    model_od = od.OD(od.get_scd_mm(bottom), model, state)

    output = ""

    # Render classes
    for name, class_node in model_scd.get_classes().items():
        if model_od.read_slot_boolean(class_node, "abstract"):
            output += f"\nabstract class \"{name}\" as {make_id(class_node)}"
        else:
            output += f"\nclass \"{name}\" as {make_id(class_node)}"

        # Render attributes
        output += " {"
        for (attr_name, attr_edge) in od.get_attributes(bottom, class_node):
            tgt_name = model_scd.get_class_name(bottom.read_edge_target(attr_edge))
            output += f"\n  {attr_name} : {tgt_name}"
        output += "\n}"

    output += "\n"

    # Render inheritance links
    for inh_node in model_scd.get_inheritances().values():
        src_node = bottom.read_edge_source(inh_node)
        tgt_node = bottom.read_edge_target(inh_node)
        # src_name = model_scd.get_class_name(bottom.read_edge_source(inh_node))
        # tgt_name = model_scd.get_class_name(bottom.read_edge_target(inh_node))
        output += f"\n{make_id(tgt_node)} <|-- {make_id(src_node)}"

    output += "\n"

    # Render associations
    for assoc_name, assoc_edge in model_scd.get_associations().items():
        src_node = bottom.read_edge_source(assoc_edge)
        tgt_node = bottom.read_edge_target(assoc_edge)
        # src_name = model_scd.get_class_name(bottom.read_edge_source(assoc_edge))
        # tgt_name = model_scd.get_class_name(bottom.read_edge_target(assoc_edge))

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


def render_object_diagram(state, m, mm):
    bottom = Bottom(state)
    mm_scd = scd.SCD(mm, state)
    m_od = od.OD(mm, m, state)

    output = ""

    # Render objects
    for class_name, class_node in mm_scd.get_classes().items():
        for obj_name, obj_node in m_od.get_objects(class_node).items():
            output += f"\nobject \"{obj_name} : {class_name}\" as {make_id(obj_node)}"

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

def render_trace_ramifies(state, mm, ramified_mm):
    bottom = Bottom(state)

    mm_scd = scd.SCD(mm, state)
    ramified_mm_scd = scd.SCD(ramified_mm, state)

    # output = (
    #       render_package("original", render_class_diagram(state, mm))
    #     + '\n'
    #     + render_package("RAMified", render_class_diagram(state, ramified_mm))
    # )

    output = ""

    # output += "\n"

    for ram_name, ram_class_node in ramified_mm_scd.get_classes().items():
        original_class, = bottom.read_outgoing_elements(ram_class_node, ramify.RAMIFIES_LABEL)
        original_name = mm_scd.get_class_name(original_class)
        output += f"\n{make_id(ram_class_node)} ..> {make_id(original_class)} #line:green;text:green : RAMifies "

    return output


def render_trace_conformance(state, m, mm):
    bottom = Bottom(state)
    mm_scd = scd.SCD(mm, state)
    m_od = od.OD(mm, m, state)

    output = ""

    # Render objects
    for class_name, class_node in mm_scd.get_classes().items():
        for obj_name, obj_node in m_od.get_objects(class_node).items():
            output += f"\n{make_id(obj_node)} ..> {make_id(class_node)} #line:blue;text:blue : instanceOf"

    output += '\n'

    return output

def render_trace_match(state, mapping):
    bottom = Bottom(state)

    output = ""

    for pattern_el, host_el in mapping.items():
        # only render 'match'-edges between objects (= those elements where the type of the type is 'Class'):
        if od.get_type(bottom, od.get_type(bottom, pattern_el)) == od.get_scd_mm_class_node(bottom):
            output += f"\n{make_id(pattern_el)} ..> {make_id(host_el)} #line:grey;text:grey : matchedWith"

    return output

def make_id(uuid) -> str:
    return (str(uuid).replace('-','_'))