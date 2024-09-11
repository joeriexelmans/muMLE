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

    conf = Conformance(state, dsl_mm_id, scd_mm_id)
    print("conforms?", conf.check_nominal(log=True))

    # Model in our DSL
    dsl_m_id = state.create_node()
    dsl_m_od = OD(dsl_mm_id, dsl_m_id, state)

    dsl_m_od.create_object("george", "Man")
    dsl_m_od.create_object("bear1", "Bear")
    dsl_m_od.create_object("bear2", "Bear")
    dsl_m_od.create_link("georgeAfraidOfBear1", "afraidOf", "george", "bear1")
    dsl_m_od.create_link("georgeAfraidOfBear2", "afraidOf", "george", "bear2")

    dsl_m_od.create_slot("weight", "george",
        dsl_m_od.create_integer_value("george.weight", 80))

    conf2 = Conformance(state, dsl_m_id, dsl_mm_id)
    print("Model conforms?", conf2.check_nominal(log=True))

    # RAMify MM
    ramified_mm_id = ramify(state, dsl_mm_id)

    # LHS of our rule
    lhs_id = state.create_node()
    lhs_od = OD(ramified_mm_id, lhs_id, state)

    lhs_od.create_object("man", "RAM_Man")
    lhs_od.create_slot("RAM_weight", "man", lhs_od.create_string_value("man.RAM_weight", 'v < 99'))
    lhs_od.create_object("scaryAnimal", "RAM_Animal")
    lhs_od.create_link("manAfraidOfAnimal", "RAM_afraidOf", "man", "scaryAnimal")

    conf3 = Conformance(state, lhs_id, ramified_mm_id)
    print("LHS conforms?", conf3.check_nominal(log=True))

    # RHS of our rule
    rhs_id = state.create_node()
    rhs_od = OD(ramified_mm_id, rhs_id, state)

    rhs_od.create_object("man", "RAM_Man")
    rhs_od.create_slot("RAM_weight", "man", rhs_od.create_string_value("man.RAM_weight", 'v + 5'))

    conf4 = Conformance(state, rhs_id, ramified_mm_id)
    print("RHS conforms?", conf4.check_nominal(log=True))

    # Convert to format understood by matching algorithm
    host = mvs_adapter.model_to_graph(state, dsl_m_id, dsl_mm_id)
    guest = mvs_adapter.model_to_graph(state, lhs_id, ramified_mm_id)

    print("HOST:")
    print(host.vtxs)
    print(host.edges)

    print("GUEST:")
    print(guest.vtxs)
    print(guest.edges)

    print("matching...")
    matcher = MatcherVF2(host, guest, mvs_adapter.RAMCompare(Bottom(state), dsl_m_od))
    prev = None
    for m in matcher.match():
        print("\nMATCH:\n", m)
        name_to_matched = {}
        for guest_vtx, host_vtx in m.mapping_vtxs.items():
            if isinstance(guest_vtx, mvs_adapter.NamedNode) and isinstance(host_vtx, mvs_adapter.NamedNode):
                name_to_matched[guest_vtx.name] = host_vtx.name
        print(name_to_matched)
        rewriter.rewrite(state, lhs_id, rhs_id, name_to_matched, dsl_m_id)
        break
    print("DONE")

    conf5 = Conformance(state, dsl_m_id, dsl_mm_id)
    print("Updated model conforms?", conf5.check_nominal(log=True))

if __name__ == "__main__":
    main()
