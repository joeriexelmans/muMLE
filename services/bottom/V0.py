from uuid import UUID
from state.base import State
from typing import Any, List


class Bottom:
    def __init__(self, state: State):
        self.state = state

    def create_node(self, value=None) -> UUID:
        if value is None:
            return self.state.create_node()
        else:
            return self.state.create_nodevalue(value)

    def create_edge(self, source: UUID, target: UUID, label=None):
        if label is None:
            return self.state.create_edge(source, target)
        else:
            return self.state.create_dict(source, label, target)

    def read_value(self, node: UUID) -> Any:
        return self.state.read_value(node)

    def read_edge_source(self, edge: UUID) -> UUID:
        result = self.state.read_edge(edge)
        return result[0] if result is not None else result

    def read_edge_target(self, edge: UUID) -> UUID:
        result = self.state.read_edge(edge)
        return result[1] if result is not None else result

    def read_incoming_edges(self, target: UUID, label=None) -> List[UUID]:
        def read_label(_edge: UUID):
            try:
                label_edge, = self.state.read_outgoing(_edge)
                _, tgt = self.state.read_edge(label_edge)
                _label = self.state.read_value(tgt)
                return _label
            except (TypeError, ValueError):
                return None

        edges = self.state.read_incoming(target)
        if edges is None:
            return []
        if label is not None:
            edges = [e for e in edges if read_label(e) == label]
        return edges

    def read_outgoing_edges(self, source: UUID, label=None) -> List[UUID]:
        def read_label(_edge: UUID):
            try:
                label_edge, = self.state.read_outgoing(_edge)
                _, tgt = self.state.read_edge(label_edge)
                _label = self.state.read_value(tgt)
                return _label
            except (TypeError, ValueError):
                return None

        edges = self.state.read_outgoing(source)
        if edges is None:
            return []
        if label is not None:
            edges = [e for e in edges if read_label(e) == label]
        return edges

    def read_incoming_elements(self, target: UUID, label=None) -> List[UUID]:
        edges = self.read_incoming_edges(target, label)
        if edges is None or len(edges) == 0:
            return []
        else:
            return [self.read_edge_source(e) for e in edges]

    def read_outgoing_elements(self, source: UUID, label=None) -> List[UUID]:
        edges = self.read_outgoing_edges(source, label)
        if edges is None or len(edges) == 0:
            return []
        else:
            return [self.read_edge_target(e) for e in edges]

    def read_keys(self, element: UUID) -> List[str]:
        key_nodes = self.state.read_dict_keys(element)
        unique_keys = {self.state.read_value(node) for node in key_nodes}
        return list(unique_keys)

    def delete_element(self, element: UUID):
        src, tgt = self.state.read_edge(element)
        if src is None and tgt is None:
            # node
            self.state.delete_node(element)
        else:
            # edge
            self.state.delete_edge(element)

