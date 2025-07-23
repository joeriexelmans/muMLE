"""
node.py

Defines the abstract base Node class for graph-based structures. Each Node is assigned
a unique identifier via an external IdGenerator. The class provides an interface for
managing execution state and generating DOT graph representations.
"""

from abc import abstractmethod
from jinja2 import Template
from .funcs import IdGenerator


class Node:
    """
    Abstract base class for graph nodes. Each Node has a unique ID and supports
    context-dependent state management for execution scenarios. Subclasses must
    implement the DOT graph generation logic.
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes the Node instance with a unique ID.

        Attributes:
            id (int): A unique identifier assigned by IdGenerator.
        """
        self.id: int = IdGenerator.generate_node_id()

    def get_id(self) -> int:
        """
        Retrieves the unique identifier of the node.

        Returns:
            int: The unique node ID.
        """
        return self.id

    def generate_stack_frame(self, exec_id: int) -> None:
        """
        Initializes a new state frame for a specific execution context.
        Designed to be overridden in subclasses that use execution state.

        Args:
            exec_id (int): The ID of the execution context.
        """

    def delete_stack_frame(self, exec_id: int) -> None:
        """
        Deletes the state frame for a specific execution context.
        Designed to be overridden in subclasses that use execution state.

        Args:
            exec_id (int): The ID of the execution context.
        """

    @abstractmethod
    def generate_dot(
        self, nodes: list[str], edges: list[str], visited: set[int], template: Template
    ) -> None:
        """
        Generates the DOT graph representation for this node and its relationships.

        Args:
            nodes (list[str]): A list to append DOT node definitions to.
            edges (list[str]): A list to append DOT edge definitions to.
            visited (set[int]): A set of already visited node IDs to avoid duplicates or recursion.
            template (Template): A Jinja2 template used to format the node's DOT representation.
        """
