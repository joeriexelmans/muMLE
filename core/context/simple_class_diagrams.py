from core.element import Element
from state.base import State
from core.context.generic import GenericContext


class SCDContext(GenericContext):
    def __init__(self, state: State, model: Element, metamodel: Element):
        super().__init__(state, model, metamodel)


def main():
    from state.devstate import DevState

    s = DevState()
    scd = SCDContext(s, Element(), Element())
    bootstrap = scd._bootstrap_scd()
    model = s.read_dict(bootstrap.id, "Model")
    x = []
    for e in s.read_outgoing(model):
        label_node_edge, = s.read_outgoing(e)
        _, label_node = s.read_edge(label_node_edge)
        type_node = s.read_dict(label_node, "Type")
        x.append(f"{s.read_value(label_node)} : {s.read_value(type_node)}")
    for t in sorted(x):
        print(t)

    # s.dump("out/scd.dot", "out/scd.png")


if __name__ == '__main__':
    main()
