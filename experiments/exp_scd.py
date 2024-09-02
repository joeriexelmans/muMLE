# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD

import sys

def main():
    state = DevState()
    root = state.read_root() # id: 0
    scd_node = bootstrap_scd(state)
    scd_node2 = state.read_dict(root, "SCD")
    # print(root, scd_node, scd_node2)

    def print_tree(root, max_depth, depth=0):
        print("  "*depth, "root=", root, "value=", state.read_value(root))
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
    print_tree(root, 1)

    model_id = state.create_node()
    scd = SCD(model_id, state)
    scd.create_class("A")
    scd.create_class("B")
    scd.create_association("A2B", "A", "B",
        src_min_c=1,
        src_max_c=1,
        tgt_min_c=1,
        tgt_max_c=2,
    )

    print_tree(model_id, 1)

    conf = Conformance(state, model_id, scd_node)
    print("Check nominal conformance...")
    print(conf.check_nominal(log=True))
    print("Check structural conformance...")
    print(conf.check_structural(log=True))
    print("Check nominal conformance (again)...")
    print(conf.check_nominal(log=True))

    inst_id = state.create_node()
    od = OD(model_id, inst_id, state)

    od.create_object("a", "A")
    od.create_object("b", "B")
    od.create_link("A2B", "a", "b")

    conf2 = Conformance(state, inst_id, model_id)
    print(conf2.check_nominal(log=True))

if __name__ == "__main__":
    main()
