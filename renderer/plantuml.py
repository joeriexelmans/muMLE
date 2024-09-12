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
            output += f"\nabstract class {name}"
        else:
            output += f"\nclass {name}"

        # Render attributes
        output += " {"
        for (attr_name, attr_edge) in od.get_attributes(bottom, class_node):
            tgt_name = model_scd.get_class_name(bottom.read_edge_target(attr_edge))
            output += f"\n  {attr_name} : {tgt_name}"
        output += "\n}"

    output += "\n"

    # Render inheritance links
    for inh_node in model_scd.get_inheritances().values():
        src_name = model_scd.get_class_name(bottom.read_edge_source(inh_node))
        tgt_name = model_scd.get_class_name(bottom.read_edge_target(inh_node))
        output += f"\n{tgt_name} <|-- {src_name}"

    output += "\n"

    for assoc_name, assoc_edge in model_scd.get_associations().items():
        src_name = model_scd.get_class_name(bottom.read_edge_source(assoc_edge))
        tgt_name = model_scd.get_class_name(bottom.read_edge_target(assoc_edge))

        src_lower_card, src_upper_card, tgt_lower_card, tgt_upper_card = model_scd.get_assoc_cardinalities(assoc_edge)
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
        
        output += f'\n{src_name} "{src_card}" --> "{tgt_card}" {tgt_name} : {assoc_name}'

    return output

def render_package(name, contents):
    output = ""
    output += f'\npackage "{name}" {{'
    output += contents
    output += '\n}'
    return output

def render_ramification(state, mm, ramified_mm):
    bottom = Bottom(state)

    output = (
          render_package("original", render_class_diagram(state, mm))
        + '\n'
        + render_package("RAMified", render_class_diagram(state, ramified_mm))
    )

    mm_scd = scd.SCD(mm, state)
    ramified_mm_scd = scd.SCD(ramified_mm, state)

    output += "\n"

    for ram_name, ram_class_node in ramified_mm_scd.get_classes().items():
        original_class, = bottom.read_outgoing_elements(ram_class_node, ramify.RAMIFIES_LABEL)
        original_name = mm_scd.get_class_name(original_class)
        output += f"\n{ram_name} ..> {original_name} : RAMifies"

    return output