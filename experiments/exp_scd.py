# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.ramify import ramify
from services.primitives.integer_type import Integer

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

    # scd2 = SCD(scd_node, state)
    # for el in scd2.list_elements():
    #     print(el)


    model_id = state.create_node()
    scd = SCD(model_id, state)
    scd.create_class("Abstract", abstract=True)
    scd.create_class("A", min_c=1, max_c=10)
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
    od.create_object("b", "B")
    od.create_link("A2B", "a", "b")

    od.create_slot("size", "a", od.create_integer_value(42))

    print("checking conformance....")
    conf2 = Conformance(state, inst_id, model_id)
    print("conforms?", conf2.check_nominal(log=True))

    ramify(state, model_id)

if __name__ == "__main__":
    main()
