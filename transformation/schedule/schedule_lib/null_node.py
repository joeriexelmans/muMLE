"""
null_node.py

Defines the NullNode class, a no-op singleton execution node used for open execution pins
in the object diagram execution graph.
"""

from abc import ABC
from typing import List, Type
from jinja2 import Template
from api.od import ODAPI
from .funcs import generate_dot_node
from .singleton import Singleton
from .exec_node import ExecNode

class NullNode(ExecNode, metaclass=Singleton):
    """
    A no-op execution node representing a null operation.

    This node is typically used to represent a placeholder or open execution pin.
    It always returns a fixed result and does not perform any operation.
    """

    def __init__(self):
        """
        Initializes the NullNode instance.
        Inherits unique ID and state behavior from ExecNode.
        """
        super().__init__()

    def execute(self, port: str, exec_id: int, od: ODAPI) -> tuple[int, any] | None:
        """
        Simulates execution by returning a static result indicating an open pin.

        Args:
            port (str): The name of the input port.
            exec_id (int): The current execution ID.
            od (ODAPI): The Object Diagram API instance providing execution context.

        Returns:
            tuple[int, str] | None: A tuple (-1, "open pin reached") indicating a no-op.
        """
        return -1, "open pin reached"

    @staticmethod
    def get_exec_output_gates():
        """
        Returns the list of output gates for execution.

        Returns:
            list: An empty list, as NullNode has no output gates.
        """
        return []

    def generate_dot(
        self, nodes: List[str], edges: List[str], visited: set[int], template: Template
    ) -> None:
        """
        Generates DOT graph representation for this node if it hasn't been visited.

        Args:
            nodes (List[str]): A list to accumulate DOT node definitions.
            edges (List[str]): A list to accumulate DOT edge definitions.
            visited (set[int]): Set of already visited node IDs to avoid cycles.
            template (Template): A Jinja2 template used to render the node's DOT representation.
        """
        if self.id in visited:
            return
        generate_dot_node(
            self,
            nodes,
            template,
            **{
                "label": "null",
                "ports_exec": (
                    self.get_exec_input_gates(),
                    self.get_exec_output_gates(),
                ),
            }
        )
