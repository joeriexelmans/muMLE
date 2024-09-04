from typing import Any, Optional, List, Tuple, Callable, Generator
from neo4j import GraphDatabase
from ast import literal_eval

from .base import State, Edge, Node, Element, UUID



class Neo4jState(State):
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="tests"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.root = self.create_node()

    def close(self, *, clear=False):
        if clear:
            self._run_and_return(self._clear)
        self.driver.close()

    def _run_and_return(self, query: Callable, **kwargs):
        with self.driver.session() as session:
            result = session.write_transaction(query, **kwargs)
            return result

    @staticmethod
    def _clear(tx):
        tx.run("MATCH (n) "
               "DETACH DELETE n")

    @staticmethod
    def _existence_check(tx, eid, label="Element"):
        result = tx.run(f"MATCH (elem:{label}) "
                        "WHERE elem.id = $eid "
                        "RETURN elem.id",
                        eid=eid)
        try:
            return result.single()[0]
        except TypeError:
            # No node found for nid
            # ergo, no edge created
            return None

    def create_node(self) -> Node:
        def query(tx, nid):
            result = tx.run("CREATE (n:Element:Node) "
                            "SET n.id = $nid "
                            "RETURN n.id",
                            nid=nid)
            return result.single()[0]

        node = self._run_and_return(query, nid=str(self.new_id()))
        return UUID(node) if node != None else None

    def create_edge(self, source: Element, target: Element) -> Optional[Edge]:
        def query(tx, eid, sid, tid):
            result = tx.run("MATCH (source), (target) "
                            "WHERE source.id = $sid AND target.id = $tid "
                            "CREATE (source) -[:Source]-> (e:Element:Edge) -[:Target]-> (target) "
                            "SET e.id = $eid "
                            "RETURN e.id",
                            eid=eid, sid=sid, tid=tid)
            try:
                return result.single()[0]
            except TypeError:
                # No node found for sid and/or tid
                # ergo, no edge created
                return None

        edge = self._run_and_return(query, eid=str(self.new_id()), sid=str(source), tid=str(target))
        return UUID(edge) if edge != None else None

    def create_nodevalue(self, value: Any) -> Optional[Node]:
        def query(tx, nid, val):
            result = tx.run("CREATE (n:Element:Node) "
                            "SET n.id = $nid, n.value = $val "
                            "RETURN n.id",
                            nid=nid, val=val)
            return result.single()[0]

        if not self.is_valid_datavalue(value):
            return None

        node = self._run_and_return(query, nid=str(self.new_id()), val=repr(value))
        return UUID(node) if node != None else None

    def create_dict(self, source: Element, value: Any, target: Element) -> Optional[Tuple[Edge, Edge, Node]]:
        if not self.is_valid_datavalue(value):
            return None

        edge_node = self.create_edge(source, target)
        val_node = self.create_nodevalue(value)
        if edge_node != None and val_node != None:
            self.create_edge(edge_node, val_node)

    def read_root(self) -> Node:
        return self.root

    def read_value(self, node: Node) -> Optional[Any]:
        def query(tx, nid):
            result = tx.run("MATCH (n:Node) "
                            "WHERE n.id = $nid "
                            "RETURN n.value",
                            nid=nid)
            try:
                return result.single()[0]
            except TypeError:
                # No node found for nid
                return None

        value = self._run_and_return(query, nid=str(node))
        return literal_eval(value) if value != None else None

    def read_outgoing(self, elem: Element) -> Optional[List[Edge]]:
        def query(tx, eid):
            result = tx.run("MATCH (elem:Element) -[:Source]-> (e:Edge) "
                            "WHERE elem.id = $eid "
                            "RETURN e.id",
                            eid=eid)
            return result.value()

        source_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if source_exists:
            result = self._run_and_return(query, eid=str(elem))
            return [UUID(x) for x in result] if result != None else None

    def read_incoming(self, elem: Element) -> Optional[List[Edge]]:
        def query(tx, eid):
            result = tx.run("MATCH (elem:Element) <-[:Target]- (e:Edge) "
                            "WHERE elem.id = $eid "
                            "RETURN e.id",
                            eid=eid)
            return result.value()

        target_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if target_exists:
            result = self._run_and_return(query, eid=str(elem))
            return [UUID(x) for x in result] if result != None else None

    def read_edge(self, edge: Edge) -> Tuple[Optional[Node], Optional[Node]]:
        def query(tx, eid):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (tgt)"
                            "WHERE e.id = $eid "
                            "RETURN src.id, tgt.id",
                            eid=eid)
            return result.single()

        edge_exists = self._run_and_return(self._existence_check, eid=str(edge), label="Edge") != None
        if edge_exists:
            try:
                src, tgt = self._run_and_return(query, eid=str(edge))
                return UUID(src), UUID(tgt)
            except TypeError:
                return None, None
        else:
            return None, None

    def read_dict(self, elem: Element, value: Any) -> Optional[Element]:
        def query(tx, eid, label_value):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (tgt), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE src.id = $eid "
                            "AND label.value = $val "
                            "RETURN tgt.id",
                            eid=eid, val=label_value)
            try:
                return result.single()[0]
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            if isinstance(value, UUID):
                return None
            result = self._run_and_return(query, eid=str(elem), label_value=repr(value))
            return UUID(result) if result != None else None

    def read_dict_keys(self, elem: Element) -> Optional[List[Any]]:
        def query(tx, eid):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE src.id = $eid "
                            "RETURN label.id",
                            eid=eid)
            try:
                return result.value()
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            result = self._run_and_return(query, eid=str(elem))
            return [UUID(x) for x in result if x != None]

    def read_dict_edge(self, elem: Element, value: Any) -> Optional[Edge]:
        def query(tx, eid, label_value):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE src.id = $eid "
                            "AND label.value = $val "
                            "RETURN e.id",
                            eid=eid, val=label_value)
            try:
                return result.single()[0]
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            result = self._run_and_return(query, eid=str(elem), label_value=repr(value))
            return UUID(result) if result != None else None

    def read_dict_node(self, elem: Element, value_node: Node) -> Optional[Element]:
        def query(tx, eid, label_id):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (tgt), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE src.id = $eid "
                            "AND label.id = $lid "
                            "RETURN tgt.id",
                            eid=eid, lid=label_id)
            try:
                return result.single()[0]
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            result = self._run_and_return(query, eid=str(elem), label_id=str(value_node))
            return UUID(result) if result != None else None

    def read_dict_node_edge(self, elem: Element, value_node: Node) -> Optional[Edge]:
        def query(tx, eid, label_id):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE src.id = $eid "
                            "AND label.id = $lid "
                            "RETURN e.id",
                            eid=eid, lid=label_id)
            try:
                return result.single()[0]
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            result = self._run_and_return(query, eid=str(elem), label_id=str(value_node))
            return UUID(result) if result != None else None

    def read_reverse_dict(self, elem: Element, value: Any) -> Optional[List[Element]]:
        def query(tx, eid, label_value):
            result = tx.run("MATCH (src) -[:Source]-> (e:Edge) -[:Target]-> (tgt), "
                            "(e) -[:Source]-> (:Edge) -[:Target]-> (label)"
                            "WHERE tgt.id = $eid "
                            "AND label.value = $val "
                            "RETURN src.id",
                            eid=eid, val=label_value)
            try:
                return result.value()
            except TypeError:
                # No edge found with given label
                return None

        elem_exists = self._run_and_return(self._existence_check, eid=str(elem)) != None
        if elem_exists:
            result = self._run_and_return(query, eid=str(elem), label_value=repr(value))
            return [UUID(x) for x in result if x != None]

    def delete_node(self, node: Node) -> None:
        def query(tx, nid):
            result = tx.run("MATCH (n:Node) "
                            "WHERE n.id = $nid "
                            "OPTIONAL MATCH (n) -- (e:Edge) "
                            "DETACH DELETE n "
                            "RETURN e.id",
                            nid=nid)
            return result.value()

        to_be_deleted = self._run_and_return(query, nid=str(node))
        to_be_deleted = [UUID(x) for x in to_be_deleted if x != None]
        for edge in to_be_deleted:
            self.delete_edge(edge)

    def delete_edge(self, edge: Edge) -> None:
        def query(tx, eid):
            result = tx.run("MATCH (e1:Edge) "
                            "WHERE e1.id = $eid "
                            "OPTIONAL MATCH (e1) -- (e2:Edge) "
                            "WHERE (e1) -[:Source]-> (e2) "
                            "OR (e1) <-[:Target]- (e2) "
                            "DETACH DELETE e1 "
                            "RETURN e2.id",
                            eid=eid)
            return result.value()

        to_be_deleted = self._run_and_return(query, eid=str(edge))
        to_be_deleted = [UUID(x) for x in to_be_deleted if x != None]
        for edge in to_be_deleted:
            self.delete_edge(edge)
