# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.ramify import ramify
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
    scd_node = bootstrap_scd(state)
    scd_node2 = state.read_dict(root, "SCD")
    # print(root, scd_node, scd_node2)

    def print_tree(root, max_depth, depth=0):
        print("  "*depth, "root=", root, "value=", state.read_value(root))
        src,tgt = state.read_edge(root)
        if src != None:
            print("  "*depth, "src...")
            print_tree(src, max_depth, depth+1)
        if tgt != None:
            print("  "*depth, "tgt...")
            print_tree(tgt, max_depth, depth+1)
        for edge in state.read_outgoing(root):
            for edge_label in state.read_outgoing(edge):
                [_,tgt] = state.read_edge(edge_label)
                label = state.read_value(tgt)
                print("  "*depth, " key:", label)
            [_, tgt] = state.read_edge(edge)
            value = state.read_value(tgt)
            if value != None:
                print("  "*depth, " ->", tgt, " (value:", value, ")")
            else:
                print("  "*depth, " ->", tgt)
            if depth < max_depth:
                if isinstance(value, str) and len(value) == 36:
                    i = None
                    try:
                        i = UUID(value)
                    except ValueError as e:
                        # print("invalid UUID:", value)
                        pass
                    if i != None:
                        print_tree(i, max_depth, depth+1)
                print_tree(tgt, max_depth, depth+1)

    print("explore...")
    # print_tree(root, 2)

    int_type_id = state.read_dict(state.read_root(), "Integer")
    int_type = UUID(state.read_value(int_type_id))

    string_type_id = state.read_dict(state.read_root(), "String")
    string_type = UUID(state.read_value(string_type_id))

    # scd2 = SCD(scd_node, state)
    # for el in scd2.list_elements():
    #     print(el)


    model_id = state.create_node()
    scd = SCD(model_id, state)
    scd.create_class("Abstract", abstract=True)
    scd.create_class("A", min_c=1, max_c=2)
    scd.create_inheritance("A", "Abstract")
    scd.create_model_ref("Integer", int_type)
    scd.create_attribute_link("A", "Integer", "size", False)
    scd.create_class("B")
    scd.create_association("A2B", "A", "B",
        src_min_c=1,
        src_max_c=1,
        tgt_min_c=1,
        tgt_max_c=2,
    )

    # print_tree(model_id, 3)


    conf = Conformance(state, model_id, scd_node)
    print("Check nominal conformance...")
    print(conf.check_nominal(log=True))
    # print("Check structural conformance...")
    # print(conf.check_structural(log=True))
    # print("Check nominal conformance (again)...")
    # print(conf.check_nominal(log=True))

    inst_id = state.create_node()
    od = OD(model_id, inst_id, state)

    od.create_object("a", "A")
    od.create_object("a2", "A")
    od.create_object("b", "B")
    od.create_link("A2B", "a", "b")
    od.create_link("A2B", "a2", "b")

    od.create_slot("size", "a", od.create_integer_value("a.size", 42))

    print("checking conformance....")
    conf2 = Conformance(state, inst_id, model_id)
    print("conforms?", conf2.check_nominal(log=True))

    ramified_MM_id = ramify(state, model_id)

    pattern_id = state.create_node()
    pattern = OD(ramified_MM_id, pattern_id, state)

    pattern.create_object("a1", "A")
    pattern.create_slot("size", "a1", pattern.create_string_value("a1.size", 'v < 100'))
    # pattern.create_object("a2", "A")
    # pattern.create_slot("size", "a2", pattern.create_string_value("a2.size", '99'))

    pattern.create_object("b1", "B")
    # pattern.create_link("A2B", "a1", "b1")

    conf3 = Conformance(state, pattern_id, ramified_MM_id)
    print("conforms?", conf3.check_nominal(log=True))

    host = mvs_adapter.model_to_graph(state, inst_id)
    guest = mvs_adapter.model_to_graph(state, pattern_id)

    print(host.vtxs)
    print(host.edges)

    print("matching...")
    matcher = MatcherVF2(host, guest, mvs_adapter.RAMCompare(Bottom(state)))
    prev = None
    for m in matcher.match():
        print("\nMATCH:\n", m)
        input()
    print("DONE")

if __name__ == "__main__":
    main()
