from typing import Any, List, Tuple, Optional, Generator
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.plugins.sparql import prepareQuery
import json

from .base import State

# Define graph datasctructures used by implementation
# Use NewType to create distinct type or just create a type alias
Element = URIRef
Node = URIRef
Edge = URIRef


class RDFState(State):
    def __init__(self, namespace_uri="http://modelverse.mv/#"):
        self.graph = Graph()
        self.namespace_uri = namespace_uri
        self.mv = Namespace(namespace_uri)
        self.graph.bind("MV", self.mv)
        self.prepared_queries = {
            "read_value": """
                            SELECT ?value
                            WHERE {
                                ?var1 MV:hasValue ?value .
                            }
                          """,
            "read_outgoing": """
                            SELECT ?link
                            WHERE {
                                ?link MV:hasSource ?var1 .
                            }
                            """,
            "read_incoming": """
                            SELECT ?link
                            WHERE {
                                ?link MV:hasTarget ?var1 .
                            }
                            """,
            "read_edge": """
                            SELECT ?source ?target
                            WHERE {
                                ?var1 MV:hasSource ?source ;
                                      MV:hasTarget ?target .
                            }
                            """,
            "read_dict_keys": """
                            SELECT ?key
                            WHERE {
                                ?main_edge MV:hasSource ?var1 .
                                ?attr_edge MV:hasSource ?main_edge ;
                                           MV:hasTarget ?key .
                            }
                            """,
            "read_dict_node": """
                            SELECT ?value_node
                            WHERE {
                                ?main_edge MV:hasSource ?var1 ;
                                           MV:hasTarget ?value_node .
                                ?attr_edge MV:hasSource ?main_edge ;
                                           MV:hasTarget ?var2 .
                            }
                            """,
            "read_dict_node_edge": """
                            SELECT ?main_edge
                            WHERE {
                                ?main_edge MV:hasSource ?var1 .
                                ?attr_edge MV:hasSource ?main_edge ;
                                           MV:hasTarget ?var2 .
                            }
                            """,
            "delete_node": """
                            SELECT ?edge
                            WHERE {
                                { ?edge MV:hasTarget ?var1 . }
                                UNION
                                { ?edge MV:hasSource ?var1 . }
                            }
                            """,
            "delete_edge": """
                            SELECT ?edge
                            WHERE {
                                { ?edge MV:hasTarget ?var1 . }
                                UNION
                                { ?edge MV:hasSource ?var1 . }
                            }
                            """,
        }
        self.garbage = set()

        for k, v in list(self.prepared_queries.items()):
            self.prepared_queries[k] = prepareQuery(self.prepared_queries[k], initNs={"MV": self.mv})

        self.root = self.create_node()

    def create_node(self) -> Node:
        return URIRef(self.namespace_uri + str(self.new_id()))

    def create_edge(self, source: Element, target: Element) -> Optional[Edge]:
        if not isinstance(source, URIRef):
            return None
        elif not isinstance(target, URIRef):
            return None
        edge = URIRef(self.namespace_uri + str(self.new_id()))
        self.graph.add((edge, self.mv.hasSource, source))
        self.graph.add((edge, self.mv.hasTarget, target))
        return edge

    def create_nodevalue(self, value: Any) -> Optional[Node]:
        if not self.is_valid_datavalue(value):
            return None
        node = URIRef(self.namespace_uri + str(self.new_id()))
        if isinstance(value, tuple):
            value = {"Type": value[0]}
        self.graph.add((node, self.mv.hasValue, Literal(json.dumps(value))))
        return node

    def create_dict(self, source: Element, value: Any, target: Element) -> Optional[Tuple[Edge, Edge, Node]]:
        if not isinstance(source, URIRef):
            return
        if not isinstance(target, URIRef):
            return
        if not self.is_valid_datavalue(value):
            return

        n = self.create_nodevalue(value)
        e = self.create_edge(source, target)
        self.create_edge(e, n)

    def read_root(self) -> Node:
        return self.root

    def read_value(self, node: Node) -> Optional[Any]:
        if not isinstance(node, URIRef) or not (node, None, None) in self.graph:
            return None
        result = self.graph.query(self.prepared_queries["read_value"], initBindings={"var1": node})
        if len(result) == 0:
            return None
        result = json.loads(list(result)[0][0])
        return result if not isinstance(result, dict) else (result["Type"],)

    def read_outgoing(self, elem: Element) -> Optional[List[Edge]]:
        if not isinstance(elem, URIRef) or elem in self.garbage:
            return None
        result = self.graph.query(self.prepared_queries["read_outgoing"], initBindings={"var1": elem})
        return [i[0] for i in result]

    def read_incoming(self, elem: Element) -> Optional[List[Edge]]:
        if not isinstance(elem, URIRef) or elem in self.garbage:
            return None
        result = self.graph.query(self.prepared_queries["read_incoming"], initBindings={"var1": elem})
        return [i[0] for i in result]

    def read_edge(self, edge: Edge) -> Tuple[Optional[Node], Optional[Node]]:
        if not isinstance(edge, URIRef) or not (edge, None, None) in self.graph:
            return None, None
        result = self.graph.query(self.prepared_queries["read_edge"], initBindings={"var1": edge})
        if len(result) == 0:
            return None, None
        else:
            return list(result)[0][0], list(result)[0][1]

    def read_dict(self, elem: Element, value: Any) -> Optional[Element]:
        if not isinstance(elem, URIRef):
            return None
        q = f"""
            SELECT ?value_node
            WHERE {{
                ?main_edge MV:hasSource <{elem}> ;
                           MV:hasTarget ?value_node .
                ?attr_edge MV:hasSource ?main_edge ;
                           MV:hasTarget ?attr_node .
                ?attr_node MV:hasValue '{json.dumps(value)}' .
            }}
            """
        result = self.graph.query(q)
        if len(result) == 0:
            return None
        return list(result)[0][0]

    def read_dict_keys(self, elem: Element) -> Optional[List[Any]]:
        if not isinstance(elem, URIRef):
            return None
        result = self.graph.query(self.prepared_queries["read_dict_keys"], initBindings={"var1": elem})
        return [i[0] for i in result]

    def read_dict_edge(self, elem: Element, value: Any) -> Optional[Edge]:
        if not isinstance(elem, URIRef):
            return None
        result = self.graph.query(
            f"""
            SELECT ?main_edge
            WHERE {{
                ?main_edge MV:hasSource <{elem}> ;
                           MV:hasTarget ?value_node .
                ?attr_edge MV:hasSource ?main_edge ;
                           MV:hasTarget ?attr_node .
                ?attr_node MV:hasValue '{json.dumps(value)}' .
            }}
            """)
        if len(result) == 0:
            return None
        return list(result)[0][0]

    def read_dict_node(self, elem: Element, value_node: Node) -> Optional[Element]:
        if not isinstance(elem, URIRef):
            return None
        if not isinstance(value_node, URIRef):
            return None
        result = self.graph.query(
            self.prepared_queries["read_dict_node"], initBindings={"var1": elem, "var2": value_node}
        )
        if len(result) == 0:
            return None
        return list(result)[0][0]

    def read_dict_node_edge(self, elem: Element, value_node: Node) -> Optional[Edge]:
        if not isinstance(elem, URIRef):
            return None
        if not isinstance(value_node, URIRef):
            return None
        result = self.graph.query(
            self.prepared_queries["read_dict_node_edge"], initBindings={"var1": elem, "var2": value_node}
        )
        if len(result) == 0:
            return None
        return list(result)[0][0]

    def read_reverse_dict(self, elem: Element, value: Any) -> Optional[List[Element]]:
        if not isinstance(elem, URIRef):
            return None
        result = self.graph.query(
            f"""
            SELECT ?source_node
            WHERE {{
                ?main_edge MV:hasTarget <{elem}> ;
                           MV:hasSource ?source_node .
                ?attr_edge MV:hasSource ?main_edge ;
                           MV:hasTarget ?value_node .
                ?value_node MV:hasValue '{json.dumps(value)}' .
            }}
            """)

        return [i[0] for i in result]

    def delete_node(self, node: Node) -> None:
        if node == self.root:
            return
        if not isinstance(node, URIRef):
            return
        # Check whether node isn't an edge
        if (node, self.mv.hasSource, None) in self.graph or (node, self.mv.hasTarget, None) in self.graph:
            return
        # Remove its value if it exists
        self.graph.remove((node, None, None))
        # Get all edges connecting this
        result = self.graph.query(self.prepared_queries["delete_node"], initBindings={"var1": node})
        # ... and remove them
        for e in result:
            self.delete_edge(e[0])
        self.garbage.add(node)

    def delete_edge(self, edge: Edge) -> None:
        if not isinstance(edge, URIRef):
            return
        # Check whether edge is actually an edge
        if not ((edge, self.mv.hasSource, None) in self.graph and (edge, self.mv.hasTarget, None) in self.graph):
            return
        # Remove its links
        self.graph.remove((edge, None, None))
        # Get all edges connecting this
        result = self.graph.query(self.prepared_queries["delete_edge"], initBindings={"var1": edge})
        # ... and remove them
        for e in result:
            self.delete_edge(e[0])
        self.garbage.add(edge)
