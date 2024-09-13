# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.ramify import ramify
from transformation import rewriter
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from pattern_matching import mvs_adapter
from pattern_matching.matcher import MatcherVF2
from renderer import plantuml

import sys

def create_integer_node(state, i: int):
    node = state.create_node()
    integer_t = Integer(node, state)
    integer_t.create(i)
    return node

def main():
    state = DevState()
    root = state.read_root() # id: 0

    scd_mm_id = bootstrap_scd(state)
    int_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "Integer")))
    string_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "String")))

    # def print_tree(root, max_depth, depth=0):
    #     print("  "*depth, "root=", root, "value=", state.read_value(root))
    #     src,tgt = state.read_edge(root)
    #     if src != None:
    #         print("  "*depth, "src...")
    #         print_tree(src, max_depth, depth+1)
    #     if tgt != None:
    #         print("  "*depth, "tgt...")
    #         print_tree(tgt, max_depth, depth+1)
    #     for edge in state.read_outgoing(root):
    #         for edge_label in state.read_outgoing(edge):
    #             [_,tgt] = state.read_edge(edge_label)
    #             label = state.read_value(tgt)
    #             print("  "*depth, " key:", label)
    #         [_, tgt] = state.read_edge(edge)
    #         value = state.read_value(tgt)
    #         if value != None:
    #             print("  "*depth, " ->", tgt, " (value:", value, ")")
    #         else:
    #             print("  "*depth, " ->", tgt)
    #         if depth < max_depth:
    #             if isinstance(value, str) and len(value) == 36:
    #                 i = None
    #                 try:
    #                     i = UUID(value)
    #                 except ValueError as e:
    #                     # print("invalid UUID:", value)
    #                     pass
    #                 if i != None:
    #                     print_tree(i, max_depth, depth+1)
    #             print_tree(tgt, max_depth, depth+1)

    # Meta-model for our DSL
    dsl_mm_id = state.create_node()
    dsl_mm_scd = SCD(dsl_mm_id, state)
    dsl_mm_scd.create_class("Animal", abstract=True)
    dsl_mm_scd.create_class("Man", min_c=1, max_c=2)
    dsl_mm_scd.create_inheritance("Man", "Animal")
    dsl_mm_scd.create_model_ref("Integer", int_mm_id)
    dsl_mm_scd.create_attribute_link("Man", "Integer", "weight", optional=False)
    dsl_mm_scd.create_class("Bear")
    dsl_mm_scd.create_inheritance("Bear", "Animal")
    dsl_mm_scd.create_association("afraidOf", "Man", "Animal",
        # Every Man afraid of at least one Animal:
        src_min_c=0,
        src_max_c=None,
        tgt_min_c=1,
        tgt_max_c=None,
    )

    print(dsl_mm_scd.list_elements())

    conf = Conformance(state, dsl_mm_id, scd_mm_id)
    print("conforms?", conf.check_nominal(log=True))

    # Model in our DSL
    dsl_m_id = state.create_node()
    dsl_m_od = OD(dsl_mm_id, dsl_m_id, state)

    # dsl_m_od.create_object("animal", "Animal")
    dsl_m_od.create_object("george", "Man")
    dsl_m_od.create_slot("weight", "george",
        dsl_m_od.create_integer_value("george.weight", 80))

    # "george_weight"

    dsl_m_od.create_object("bear1", "Bear")
    dsl_m_od.create_object("bear2", "Bear")
    dsl_m_od.create_link("georgeAfraidOfBear1", "afraidOf", "george", "bear1")
    dsl_m_od.create_link("georgeAfraidOfBear2", "afraidOf", "george", "bear2")


    conf2 = Conformance(state, dsl_m_id, dsl_mm_id)
    print("DSL instance conforms?", conf2.check_nominal(log=True))
    print(conf2.type_mapping)

    # RAMify MM
    prefix = "RAM_" # all ramified types can be prefixed to distinguish them a bit more
    ramified_mm_id = ramify(state, dsl_mm_id, prefix)

    # LHS of our rule
    lhs_id = state.create_node()
    lhs_od = OD(ramified_mm_id, lhs_id, state)

    lhs_od.create_object("man", prefix+"Man")
    lhs_od.create_slot(prefix+"weight", "man", lhs_od.create_string_value(f"man.{prefix}weight", 'v < 99'))
    lhs_od.create_object("scaryAnimal", prefix+"Animal")
    lhs_od.create_link("manAfraidOfAnimal", prefix+"afraidOf", "man", "scaryAnimal")

    conf3 = Conformance(state, lhs_id, ramified_mm_id)
    print("LHS conforms?", conf3.check_nominal(log=True))

    # RHS of our rule
    rhs_id = state.create_node()
    rhs_od = OD(ramified_mm_id, rhs_id, state)

    rhs_od.create_object("man", prefix+"Man")
    rhs_od.create_slot(prefix+"weight", "man", rhs_od.create_string_value(f"man.{prefix}weight", 'v + 5'))

    rhs_od.create_object("bill", prefix+"Man")
    rhs_od.create_slot(prefix+"weight", "bill", rhs_od.create_string_value(f"bill.{prefix}weight", '100'))

    rhs_od.create_link("billAfraidOfMan", prefix+"afraidOf", "bill", "man")

    conf4 = Conformance(state, rhs_id, ramified_mm_id)
    print("RHS conforms?", conf4.check_nominal(log=True))

    def render_ramification():
        uml = (""
            # Render original and RAMified meta-models
            + plantuml.render_package("Meta-Model", plantuml.render_class_diagram(state, dsl_mm_id))
            + plantuml.render_package("RAMified Meta-Model", plantuml.render_class_diagram(state, ramified_mm_id))

            # Render RAMification traceability links
            + plantuml.render_trace_ramifies(state, dsl_mm_id, ramified_mm_id)
        )

        # Render pattern
        uml += plantuml.render_package("LHS", plantuml.render_object_diagram(state, lhs_id, ramified_mm_id))
        uml += plantuml.render_trace_conformance(state, lhs_id, ramified_mm_id)

        # Render pattern
        uml += plantuml.render_package("RHS", plantuml.render_object_diagram(state, rhs_id, ramified_mm_id))
        uml += plantuml.render_trace_conformance(state, rhs_id, ramified_mm_id)

        return uml

    def render_all_matches():
        uml = render_ramification()
        # Render host graph (before rewriting)
        uml += plantuml.render_package("Model (before rewrite)", plantuml.render_object_diagram(state, dsl_m_id, dsl_mm_id))
        # Render conformance
        uml += plantuml.render_trace_conformance(state, dsl_m_id, dsl_mm_id)

        print("matching...")
        generator = mvs_adapter.match_od(state, dsl_m_id, dsl_mm_id, lhs_id, ramified_mm_id)
        for name_mapping, color in zip(generator, ["red", "orange"]):
            print("\nMATCH:\n", name_mapping)

            # Render every match
            uml += plantuml.render_trace_match(state, name_mapping, lhs_id, dsl_m_id, color)

        print("DONE")
        return uml

    def render_rewrite():
        uml = render_ramification()

        generator = mvs_adapter.match_od(state, dsl_m_id, dsl_mm_id, lhs_id, ramified_mm_id)
        for name_mapping in generator:
            rewriter.rewrite(state, lhs_id, rhs_id, ramified_mm_id, name_mapping, dsl_m_id, dsl_mm_id)

            # Render match
            uml_match = plantuml.render_trace_match(state, name_mapping, rhs_id, dsl_m_id)

            # Stop matching after rewrite
            break

        # Render host graph (after rewriting)
        uml += plantuml.render_package("Model (after rewrite)", plantuml.render_object_diagram(state, dsl_m_id, dsl_mm_id))
        # Render conformance
        uml += plantuml.render_trace_conformance(state, dsl_m_id, dsl_mm_id)

        uml += uml_match

        return uml

    conf5 = Conformance(state, dsl_m_id, dsl_mm_id)
    print("Updated model conforms?", conf5.check_nominal(log=True))

    print()
    print("==============================================")

    print(render_all_matches())
    # print(render_rewrite())


if __name__ == "__main__":
    main()
