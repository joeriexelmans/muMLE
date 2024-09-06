from typing import Any, List, Tuple, Optional

from state.base import State, Node, Edge, Element


class PyState(State):
    """
    State interface implemented using Python data structures.

    This code is based on:
    https://msdl.uantwerpen.be/git/yentl/modelverse/src/master/state/modelverse_state/main.py
    """
    def __init__(self):
        self.edges = {}
        self.outgoing = {}
        self.incoming = {}
        self.values = {}
        self.nodes = set()
        # Set used for garbage collection
        self.GC = True
        self.to_delete = set()

        self.cache = {}
        self.cache_node = {}

        self.root = self.create_node()

    def create_node(self) -> Node:
        new_id = self.new_id()
        self.nodes.add(new_id)
        return new_id

    def create_edge(self, source: Element, target: Element) -> Optional[Edge]:
        if source not in self.edges and source not in self.nodes:
            return None
        elif target not in self.edges and target not in self.nodes:
            return None
        else:
            new_id = self.new_id()
            self.outgoing.setdefault(source, set()).add(new_id)
            self.incoming.setdefault(target, set()).add(new_id)
            self.edges[new_id] = (source, target)
            if source in self.edges:
                # We are creating something dict_readable
                # Fill in the cache already!
                dict_source, dict_target = self.edges[source]
                if target in self.values:
                    self.cache.setdefault(dict_source, {})[self.values[target]] = source
                self.cache_node.setdefault(dict_source, {})[target] = source
            return new_id

    def create_nodevalue(self, value: Any) -> Optional[Node]:
        if not self.is_valid_datavalue(value):
            return None
        new_id = self.new_id()
        self.values[new_id] = value
        self.nodes.add(new_id)
        return new_id

    def create_dict(self, source: Element, value: Any, target: Element) -> None:
        if source not in self.nodes and source not in self.edges:
            return None
        elif target not in self.nodes and target not in self.edges:
            return None
        elif not self.is_valid_datavalue(value):
            return None
        else:
            n = self.create_nodevalue(value)
            e = self.create_edge(source, target)
            assert n != None and e != None
            e2 = self.create_edge(e, n)
            self.cache.setdefault(source, {})[value] = e
            self.cache_node.setdefault(source, {})[n] = e

    def read_root(self) -> Node:
        return self.root

    def read_value(self, node: Node) -> Any:
        if node in self.values:
            return self.values[node]
        else:
            return None

    def read_outgoing(self, elem: Element) -> Optional[List[Edge]]:
        if elem in self.edges or elem in self.nodes:
            if elem in self.outgoing:
                return list(self.outgoing[elem])
            else:
                return []
        else:
            return None

    def read_incoming(self, elem: Element) -> Optional[List[Edge]]:
        if elem in self.edges or elem in self.nodes:
            if elem in self.incoming:
                return list(self.incoming[elem])
            else:
                return []
        else:
            return None

    def read_edge(self, edge: Edge) -> Tuple[Optional[Element], Optional[Element]]:
        if edge in self.edges:
            return self.edges[edge][0], self.edges[edge][1]
        else:
            return None, None

    def is_edge(self, elem: Element) -> bool:
        return elem in self.edges

    def read_dict(self, elem: Element, value: Any) -> Optional[Element]:
        e = self.read_dict_edge(elem, value)
        if e == None:
            return None
        else:
            return self.edges[e][1]

    def read_dict_keys(self, elem: Element) -> Optional[List[Element]]:
        if elem not in self.nodes and elem not in self.edges:
            return None

        result = []
        # NOTE: cannot just use the cache here, as some keys in the cache might not actually exist;
        # we would have to check all of them anyway
        if elem in self.outgoing:
            for e1 in self.outgoing[elem]:
                if e1 in self.outgoing:
                    for e2 in self.outgoing[e1]:
                        result.append(self.edges[e2][1])
        return result

    def read_dict_edge(self, elem: Element, value: Any) -> Optional[Edge]:
        try:
            first = self.cache[elem][value]
            # Got hit, so validate
            if (self.edges[first][0] == elem) and (value in [self.values[self.edges[i][1]]
                                                             for i in self.outgoing[first]
                                                             if self.edges[i][1] in self.values]):
                return first
            # Hit but invalid now
            del self.cache[elem][value]
            return None
        except KeyError:
            return None

    def read_dict_node(self, elem: Element, value_node: Node) -> Optional[Element]:
        e = self.read_dict_node_edge(elem, value_node)
        if e == None:
            return None
        else:
            self.cache_node.setdefault(elem, {})[value_node] = e
            return self.edges[e][1]

    def read_dict_node_edge(self, elem: Element, value_node: Node) -> Optional[Edge]:
        try:
            first = self.cache_node[elem][value_node]
            # Got hit, so validate
            if (self.edges[first][0] == elem) and \
               (value_node in [self.edges[i][1] for i in self.outgoing[first]]):
                return first
            # Hit but invalid now
            del self.cache_node[elem][value_node]
            return None
        except KeyError:
            return None

    def read_reverse_dict(self, elem: Element, value: Any) -> Optional[List[Element]]:
        if elem not in self.nodes and elem not in self.edges:
            return None
        # Get all outgoing links
        matches = []
        if elem in self.incoming:
            for e1 in self.incoming[elem]:
                # For each link, we read the links that might link to a data value
                if e1 in self.outgoing:
                    for e2 in self.outgoing[e1]:
                        # Now read out the target of the link
                        target = self.edges[e2][1]
                        # And access its value
                        if target in self.values and self.values[target] == value:
                            # Found a match
                            matches.append(e1)
        return [self.edges[e][0] for e in matches]

    def delete_node(self, node: Node) -> None:
        if node == self.root:
            return
        elif node not in self.nodes:
            return

        self.nodes.remove(node)

        if node in self.values:
            del self.values[node]

        s = set()
        if node in self.outgoing:
            for e in self.outgoing[node]:
                s.add(e)
            del self.outgoing[node]
        if node in self.incoming:
            for e in self.incoming[node]:
                s.add(e)
            del self.incoming[node]

        for e in s:
            self.delete_edge(e)

        if node in self.outgoing:
            del self.outgoing[node]
        if node in self.incoming:
            del self.incoming[node]

    def delete_edge(self, edge: Edge) -> None:
        if edge not in self.edges:
            return

        s, t = self.edges[edge]
        if t in self.incoming:
            self.incoming[t].remove(edge)
        if s in self.outgoing:
            self.outgoing[s].remove(edge)

        del self.edges[edge]

        s = set()
        if edge in self.outgoing:
            for e in self.outgoing[edge]:
                s.add(e)
        if edge in self.incoming:
            for e in self.incoming[edge]:
                s.add(e)

        for e in s:
            self.delete_edge(e)

        if edge in self.outgoing:
            del self.outgoing[edge]
        if edge in self.incoming:
            del self.incoming[edge]

        if self.GC and (t in self.incoming and not self.incoming[t]) and (t not in self.edges):
            # Remove this node as well
            # Edges aren't deleted like this, as they might have a reachable target and source!
            # If they haven't, they will be removed because the source was removed.
            self.to_delete.add(t)

    def purge(self):
        while self.to_delete:
            t = self.to_delete.pop()
            if t in self.incoming and not self.incoming[t]:
                self.delete_node(t)

        values = set(self.edges)
        values.update(self.nodes)
        visit_list = [self.root]

        while visit_list:
            elem = visit_list.pop()
            if elem in values:
                # Remove it from the leftover values
                values.remove(elem)
                if elem in self.edges:
                    visit_list.extend(self.edges[elem])
                if elem in self.outgoing:
                    visit_list.extend(self.outgoing[elem])
                if elem in self.incoming:
                    visit_list.extend(self.incoming[elem])

        dset = set()
        for key in self.cache:
            if key not in self.nodes and key not in self.edges:
                dset.add(key)
        for key in dset:
            del self.cache[key]

        dset = set()
        for key in self.cache_node:
            if key not in self.nodes and key not in self.edges:
                dset.add(key)
        for key in dset:
            del self.cache_node[key]

        # All remaining elements are to be purged
        if len(values) > 0:
            while values:
                v = values.pop()
                if v in self.nodes:
                    self.delete_node(v)
