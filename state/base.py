from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional, Union
from uuid import UUID, uuid4

primitive_types = (int, float, str, bool, bytes)
INTEGER = ("Integer",)
FLOAT = ("Float",)
STRING = ("String",)
BOOLEAN = ("Boolean",)
TYPE = ("Type",)
BYTES = ("Bytes",)
type_values = (INTEGER, FLOAT, STRING, BOOLEAN, TYPE, BYTES)


Node = UUID
Edge = UUID
Element = Union[Node, Edge]


class State(ABC):
    """
    Abstract base class for MvS CRUD interface defined in:
    http://msdl.cs.mcgill.ca/people/yentl/files/thesis.pdf
    This code is based on:
    https://msdl.uantwerpen.be/git/yentl/modelverse/src/master/state/modelverse_state
    """

    @staticmethod
    def new_id() -> UUID:
        """
        Generates a new UUID
        """
        return uuid4()

    @staticmethod
    def is_valid_datavalue(value: Any) -> bool:
        """
        Checks whether value type is supported.

        Args:
            value: value whose type needs to be checked

        Returns:
            True if value type is supported, False otherwise.
        """
        if isinstance(value, tuple) and value in type_values:
            return True
        if not isinstance(value, primitive_types):
            return False
        elif isinstance(value, int) and not (-2**63 <= value <= 2**63 - 1):
            return False
        return True

    def purge(self):
        """
        Implements a garbage collection routine for implementations that don't have automatic garbage collection.
        """
        pass

    # =========================================================================
    # CREATE
    # =========================================================================

    @abstractmethod
    def create_node(self) -> Node:
        """
        Creates node.

        Returns:
            The created node.
        """
        pass

    @abstractmethod
    def create_edge(self, source: Element, target: Element) -> Optional[Edge]:
        """
        Creates edge. Source and target elements should already exist.

        Args:
            source: source element of edge
            target: target element of edge

        Returns:
            The created edge, None if source or target element doesn't exist.
        """
        pass

    @abstractmethod
    def create_nodevalue(self, value: Any) -> Optional[Node]:
        """
        Creates node containing value.

        Args:
            value: value to assign to new node

        Returns:
            The created node, None if type of value is not supported.
        """
        pass

    @abstractmethod
    def create_dict(self, source: Element, value: Any, target: Element) -> None:
        """
        Creates named edge between two graph elements.

        Args:
            source: source element of edge
            value: edge label
            target: target element of edge

        Returns:
            Nothing.
        """
        pass

    # =========================================================================
    # READ
    # =========================================================================

    @abstractmethod
    def read_root(self) -> Node:
        """
        Reads state's root node.

        Returns:
            The state's root node.
        """
        pass

    @abstractmethod
    def read_value(self, node: Node) -> Optional[Any]:
        """
        Reads value of given node.

        Args:
            node: node whose value to read

        Returns:
            I node exists, value stored in node, else None.
        """
        pass

    @abstractmethod
    def read_outgoing(self, elem: Element) -> Optional[List[Edge]]:
        """
        Retrieves edges whose source is given element.
        Args:
            elem: source element of edges to retrieve

        Returns:
            If elem exists, list of edges whose source is elem, else None.
        """
        pass

    @abstractmethod
    def read_incoming(self, elem: Element) -> Optional[List[Edge]]:
        """
        Retrieves edges whose target is given element.
        Args:
            elem: target element of edges to retrieve

        Returns:
            If elem exists, list of edges whose target is elem, else None.
        """
        pass

    @abstractmethod
    def read_edge(self, edge: Edge) -> Tuple[Optional[Node], Optional[Node]]:
        """
        Reads source and target of given edge.

        Args:
            edge: edge whose source and target to read

        Returns:
            If edge exists, tuple containing source (first) and target (second) node, else (None, None)
        """
        pass

    @abstractmethod
    def read_dict(self, elem: Element, value: Any) -> Optional[Element]:
        """
        Reads element connected to given element through edge with label = value.

        Args:
            elem: source element
            value: edge label

        Returns:
            If elem doesn't exist or no edge is found with given label, None, else target element of edge  with label = value originating from source.
        """
        pass

    @abstractmethod
    def read_dict_keys(self, elem: Element) -> Optional[List[Element]]:
        """
        Reads labels of outgoing edges starting in given node.

        Args:
            elem: source element

        Returns:
            If elem exists, list of (unique) edge labels, else None.
        """
        pass

    @abstractmethod
    def read_dict_edge(self, elem: Element, value: Any) -> Optional[Edge]:
        """
        Reads edge between two elements connected through edge with label = value.

        Args:
            elem: source element
            value: edge label

        Returns:
            If elem doesn't exist or no edge is found with given label, None, else edge with label = value originating from source.
        """
        pass

    @abstractmethod
    def read_dict_node(self, elem: Element, value_node: Node) -> Optional[Element]:
        """
        Reads element connected to given element through edge with label node = value_node.

        Args:
            elem: source element
            value_node: edge label node

        Returns:
            If elem exists, target element of edge with label stored in value_node originating from elem, else None.
        """
        pass

    @abstractmethod
    def read_dict_node_edge(self, elem: Element, value_node: Node) -> Optional[Edge]:
        """
        Reads edge connecting two elements through edge with label node = value_node.

        Args:
            elem: source element
            value_node: edge label node

        Returns:
            If elem exists, edge with label node = value_node, originating from source, else None.
        """
        pass

    @abstractmethod
    def read_reverse_dict(self, elem: Element, value: Any) -> Optional[List[Element]]:
        """
        Retrieves a list of all elements that have an outgoing edge, having label = value, towards the passed element.

        Args:
            elem: target element
            value: edge label

        Returns:
            If elem exists, list of elements with an outgoing edge with label = value towards elem, else None.
        """
        pass

    # =========================================================================
    # UPDATE
    # =========================================================================
    """
    Updates are done by performing subsequent CREATE and DELETE operations:
    http://msdl.cs.mcgill.ca/people/yentl/files/thesis.pdf
    """

    # =========================================================================
    # DELETE
    # =========================================================================

    @abstractmethod
    def delete_node(self, node: Node) -> None:
        """
        Deletes given node from state graph.
        Args:
            node: node to be deleted

        Returns:
            None
        """
        pass

    @abstractmethod
    def delete_edge(self, edge: Edge) -> None:
        """
        Deletes given edge from state graph.
        Args:
            edge: edge to be deleted

        Returns:
            None
        """
        pass
