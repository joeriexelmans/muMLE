from uuid import UUID
from state.base import State
from typing import Any, List


class Bottom:
    """
    Implements services for LTM bottom (not yet explicitly modelled).
    Implemented using the (Modelverse) state graph data structure
    """
    def __init__(self, state: State):
        self.state = state

    def create_node(self, value=None) -> UUID:
        """
        Creates a node, which optionally contains a value.

        Args:
            value: value to be stored in the node

        Returns:
            UUID of the node.
        """
        if value == None:
            return self.state.create_node()
        else:
            return self.state.create_nodevalue(value)

    def create_edge(self, source: UUID, target: UUID, label=None):
        """
        Creates an edge, which optionally is labelled.

        Args:
            source: source element of the edge
            target: target element of the edge
            label: value to label the edge with

        Returns:
            UUID of the edge.
        """
        if label == None:
            return self.state.create_edge(source, target)
        else:
            return self.state.create_dict(source, label, target)

    def read_value(self, node: UUID) -> Any:
        """
        Reads value stored in a node.

        Args:
            node: UUID of the node to read value from

        Returns:
            Value contained in the node. If no value is found, returns None
        """
        return self.state.read_value(node)

    def read_edge_source(self, edge: UUID) -> UUID:
        """
        Reads source element of an edge.

        Args:
            edge: UUID of the edge to read source element of

        Returns:
            UUID of source element of the edge
        """
        result = self.state.read_edge(edge)
        return result[0] if result != None else result

    def read_edge_target(self, edge: UUID) -> UUID:
        """
        Reads target element of an edge.

        Args:
            edge: UUID of the edge to read target element of

        Returns:
            UUID of target element of the edge
        """
        result = self.state.read_edge(edge)
        return result[1] if result != None else result

    def is_edge(self, elem: UUID) -> bool:
        return self.state.is_edge(elem)

    def read_incoming_edges(self, target: UUID, label=None) -> List[UUID]:
        """
        Reads incoming edges of an element. Optionally, filter them based on their label

        Args:
            target: UUID of the element to read incoming edges for
            label: value to filter edge labels by

        Returns:
            List of UUIDs of incoming edges
        """
        def read_label(_edge: UUID):
            try:
                label_edge, = self.state.read_outgoing(_edge)
                _, tgt = self.state.read_edge(label_edge)
                _label = self.state.read_value(tgt)
                return _label
            except (TypeError, ValueError):
                return None

        edges = self.state.read_incoming(target)
        if edges == None:
            return []
        if label != None:
            edges = [e for e in edges if read_label(e) == label]
        return edges

    def read_outgoing_edges(self, source: UUID, label=None) -> List[UUID]:
        """
        Reads outgoing edges of an element. Optionally, filter them based on their label

        Args:
            source: UUID of the element to read outgoing edges for
            label: value to filter edge labels by

        Returns:
            List of UUIDs of outgoing edges
        """

        ### PERFORMANCE OPTIMIZATION ###
        if label != None:
            fast_result = self.state.read_dict_edge_all(source, label)
            # if set(alt) != set(edges):
            #     raise Exception("WRONG", alt, edges)
            return fast_result
        ### PERFORMANCE OPTIMIZATION ###

        def read_label(_edge: UUID):
            try:
                label_edge, = self.state.read_outgoing(_edge)
                _, tgt = self.state.read_edge(label_edge)
                _label = self.state.read_value(tgt)
                return _label
            except (TypeError, ValueError):
                return None

        edges = self.state.read_outgoing(source)
        if edges == None:
            return []
        if label != None:
            edges = [e for e in edges if read_label(e) == label]



        return edges

    def read_incoming_elements(self, target: UUID, label=None) -> List[UUID]:
        """
        Reads elements connected to given element via incoming edges. 
        Optionally, filter them based on the edge label.

        Args:
            target: UUID of the element to read incoming elements for
            label: value to filter edge labels by

        Returns:
            List of UUIDs of elements connected via incoming edges
        """
        edges = self.read_incoming_edges(target, label)
        if edges == None or len(edges) == 0:
            return []
        else:
            return [self.read_edge_source(e) for e in edges]

    def read_outgoing_elements(self, source: UUID, label=None) -> List[UUID]:
        """
        Reads elements connected to given element via outgoing edges. 
        Optionally, filter them based on the edge label.

        Args:
            source: UUID of the element to read outgoing elements for
            label: value to filter edge labels by

        Returns:
            List of UUIDs of elements connected via outgoing edges
        """
        edges = self.read_outgoing_edges(source, label)
        if edges == None or len(edges) == 0:
            return []
        else:
            return [self.read_edge_target(e) for e in edges]

    def read_keys(self, element: UUID) -> List[str]:
        """
        Retrieve list of outgoing edge labels

        Args:
            element: UUID of the element to read outgoing edge labels for

        Returns:
            List of outgoing edge labels
        """
        key_nodes = self.state.read_dict_keys(element)
        unique_keys = {self.state.read_value(node) for node in key_nodes}
        return list(unique_keys)

    def delete_element(self, element: UUID):
        """
        Delete an element

        Args:
            element: UUID of the element to be deleted

        Returns:
            Nothing
        """
        src, tgt = self.state.read_edge(element)
        if src == None and tgt == None:
            # node
            self.state.delete_node(element)
        else:
            # edge
            self.state.delete_edge(element)

