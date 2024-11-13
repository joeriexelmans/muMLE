# This module contains a VF2-inspired graph matching algorithm
# It defines its own Graph type, and can be used standalone (no dependencies on the rest of muMLE framework)
# Author: Joeri Exelmans

import itertools

from util.timer import Timer

# like finding the 'strongly connected componenets', but edges are navigable in any direction
def find_connected_components(graph):
    next_component = 0
    vtx_to_component = {}
    component_to_vtxs = []
    for vtx in graph.vtxs:
        if vtx in vtx_to_component:
            continue
        vtx_to_component[vtx] = next_component
        vtxs = []
        component_to_vtxs.append(vtxs)
        add_recursively(vtx, vtxs, vtx_to_component, next_component)
        next_component += 1
    return (vtx_to_component, component_to_vtxs)

def add_recursively(vtx, vtxs: list, d: dict, component: int, already_visited: set = set()):
    if vtx in already_visited:
        return
    already_visited.add(vtx)
    vtxs.append(vtx)
    d[vtx] = component
    for edge in vtx.outgoing:
        add_recursively(edge.tgt, vtxs, d, component, already_visited)
    for edge in vtx.incoming:
        add_recursively(edge.src, vtxs, d, component, already_visited)

class Graph:
    def __init__(self):
        self.vtxs = []
        self.edges = []

class Vertex:
    def __init__(self, value):
        self.incoming = []
        self.outgoing = []
        self.value = value

    def __repr__(self):
        return f"V({self.value})"

class Edge:
    def __init__(self, src: Vertex, tgt: Vertex, label=None):
        self.src = src
        self.tgt = tgt
        self.label = label

        # Add ourselves to src/tgt vertices
        self.src.outgoing.append(self)
        self.tgt.incoming.append(self)

    def __repr__(self):
        if self.label != None:
            return f"({self.src}--{self.label}->{self.tgt})"
        else:
            return f"({self.src}->{self.tgt})"

class MatcherState:
    def __init__(self):
        self.mapping_vtxs = {} # guest -> host
        self.mapping_edges = {} # guest -> host

        self.r_mapping_vtxs = {} # host -> guest
        self.r_mapping_edges = {} # host -> guest

        self.h_unmatched_vtxs = []
        self.g_unmatched_vtxs = []

        # boundary is the most recently added (to the mapping) pair of (guest -> host) vertices
        self.boundary = None

    @staticmethod
    def make_initial(host, guest, pivot):
        state = MatcherState()
        state.h_unmatched_vtxs = [vtx for vtx in host.vtxs if vtx not in pivot.values()]
        state.g_unmatched_vtxs = [vtx for vtx in guest.vtxs if vtx not in pivot.keys()]
        state.mapping_vtxs = pivot
        state.r_mapping_vtxs = { v: k for k,v in state.mapping_vtxs.items() }
        return state

    # Grow the match set (creating a new copy)
    def grow_edge(self, host_edge, guest_edge):
        new_state = MatcherState()
        new_state.mapping_vtxs  = self.mapping_vtxs
        new_state.mapping_edges = dict(self.mapping_edges)
        new_state.mapping_edges[guest_edge] = host_edge

        new_state.r_mapping_vtxs = self.r_mapping_vtxs
        new_state.r_mapping_edges = dict(self.r_mapping_edges)
        new_state.r_mapping_edges[host_edge] = guest_edge

        new_state.h_unmatched_vtxs = self.h_unmatched_vtxs
        new_state.g_unmatched_vtxs = self.g_unmatched_vtxs

        return new_state

    # Grow the match set (creating a new copy)
    def grow_vtx(self, host_vtx, guest_vtx):
        new_state = MatcherState()
        new_state.mapping_vtxs  = dict(self.mapping_vtxs)
        new_state.mapping_vtxs[guest_vtx] = host_vtx
        new_state.mapping_edges = self.mapping_edges

        new_state.r_mapping_vtxs = dict(self.r_mapping_vtxs)
        new_state.r_mapping_vtxs[host_vtx] = guest_vtx
        new_state.r_mapping_edges = self.r_mapping_edges

        new_state.h_unmatched_vtxs = [h_vtx for h_vtx in self.h_unmatched_vtxs if h_vtx != host_vtx]
        new_state.g_unmatched_vtxs = [g_vtx for g_vtx in self.g_unmatched_vtxs if g_vtx != guest_vtx]

        new_state.boundary = (guest_vtx, host_vtx)

        return new_state

    def make_hashable(self):
        return frozenset(itertools.chain(
            ((gv,hv) for gv,hv in self.mapping_vtxs.items()),
            ((ge,he) for ge,he in self.mapping_edges.items()),
        ))

    def __repr__(self):
        # return self.make_hashable().__repr__()
        return "VTXS: "+self.mapping_vtxs.__repr__()+"\nEDGES: "+self.mapping_edges.__repr__()

class MatcherVF2:
    # Guest is the pattern
    def __init__(self, host, guest, compare_fn):
        self.host = host
        self.guest = guest
        self.compare_fn = compare_fn

        # with Timer("find_connected_components - guest"):
        self.guest_vtx_to_component, self.guest_component_to_vtxs = find_connected_components(guest)

        # print("number of guest connected components:", len(self.guest_component_to_vtxs))

    def match(self, pivot={}):
        yield from self._match(
            state=MatcherState.make_initial(self.host, self.guest, pivot),
            already_visited=set())


    def _match(self, state, already_visited, indent=0):
        # input()

        def print_debug(*args):
            pass
            # print("  "*indent, *args) # uncomment to see a trace of the matching process

        print_debug("match")

        # Keep track of the states in the search space that we already visited
        hashable = state.make_hashable()
        if hashable in already_visited:
            print_debug("    SKIP - ALREADY VISITED")
            # print_debug("   ", hashable)
            return
        # print_debug("   ", [hash(a) for a in already_visited])
        # print_debug("    ADD STATE")
        # print_debug("   ", hash(hashable))
        already_visited.add(hashable)


        if len(state.mapping_vtxs) == len(self.guest.vtxs) and len(state.mapping_edges) == len(self.guest.edges):
            print_debug("GOT MATCH:")
            print_debug(" ", state.mapping_vtxs)
            print_debug(" ", state.mapping_edges)
            yield state
            return

        def read_edge(edge, direction):
            if direction == "outgoing":
                return edge.tgt
            elif direction == "incoming":
                return edge.src
            else:
                raise Exception("wtf!")

        def attempt_grow(direction, indent):
            for g_matched_vtx, h_matched_vtx in state.mapping_vtxs.items():
                print_debug('attempt_grow', direction)
                for g_candidate_edge in getattr(g_matched_vtx, direction):
                    print_debug('g_candidate_edge:', g_candidate_edge)
                    g_candidate_vtx = read_edge(g_candidate_edge, direction)
                    # g_to_skip_vtxs.add(g_candidate_vtx)
                    if g_candidate_edge in state.mapping_edges:
                        print_debug("  skip, guest edge already matched")
                        continue # skip already matched guest edge
                    for h_candidate_edge in getattr(h_matched_vtx, direction):
                        if g_candidate_edge.label != h_candidate_edge.label:
                            print_debug("  labels differ")
                            continue
                        print_debug('h_candidate_edge:', h_candidate_edge)
                        if h_candidate_edge in state.r_mapping_edges:
                            print_debug("  skip, host edge already matched")
                            continue # skip already matched host edge
                        print_debug('grow edge', g_candidate_edge, ':', h_candidate_edge, id(g_candidate_edge), id(h_candidate_edge))
                        new_state = state.grow_edge(h_candidate_edge, g_candidate_edge)
                        h_candidate_vtx = read_edge(h_candidate_edge, direction)
                        yield from attempt_match_vtxs(
                            new_state,
                            g_candidate_vtx,
                            h_candidate_vtx,
                            indent+1)
                        print_debug('backtrack edge', g_candidate_edge, ':', h_candidate_edge, id(g_candidate_edge), id(h_candidate_edge))

        def attempt_match_vtxs(state, g_candidate_vtx, h_candidate_vtx, indent):
            print_debug('attempt_match_vtxs')
            if g_candidate_vtx in state.mapping_vtxs:
                if state.mapping_vtxs[g_candidate_vtx] != h_candidate_vtx:
                    print_debug("  nope, guest already mapped (mismatch)")
                    return # guest vtx is already mapped but doesn't match host vtx
            if h_candidate_vtx in state.r_mapping_vtxs:
                if state.r_mapping_vtxs[h_candidate_vtx] != g_candidate_vtx:
                    print_debug("  nope, host already mapped (mismatch)")
                    return # host vtx is already mapped but doesn't match guest vtx
            g_outdegree = len(g_candidate_vtx.outgoing)
            h_outdegree = len(h_candidate_vtx.outgoing)
            if g_outdegree > h_outdegree:
                print_debug("  nope, outdegree")
                return
            g_indegree = len(g_candidate_vtx.incoming)
            h_indegree = len(h_candidate_vtx.incoming)
            if g_indegree > h_indegree:
                print_debug("  nope, indegree")
                return
            if not self.compare_fn(g_candidate_vtx, h_candidate_vtx):
                print_debug("  nope, bad compare")
                return
            new_state = state.grow_vtx(
                h_candidate_vtx,
                g_candidate_vtx)
            print_debug('grow vtx', g_candidate_vtx, ':', h_candidate_vtx, id(g_candidate_vtx), id(h_candidate_vtx))
            yield from self._match(new_state, already_visited, indent+1)
            print_debug('backtrack vtx', g_candidate_vtx, ':', h_candidate_vtx, id(g_candidate_vtx), id(h_candidate_vtx))

        print_debug('preferred...')
        yield from attempt_grow('outgoing', indent+1)
        yield from attempt_grow('incoming', indent+1)

        print_debug('least preferred...')
        if state.boundary != None:
            g_boundary_vtx, _ = state.boundary
            guest_boundary_component = self.guest_vtx_to_component[g_boundary_vtx]
            # only try guest vertices that are in a different component (all vertices in the same component are already discovered via 'attempt_grow')
            guest_components_to_try = (c for i,c in enumerate(self.guest_component_to_vtxs) if i != guest_boundary_component)
            # for the host vertices however, we have to try them from all components, because different connected components of our pattern (=guest) could be mapped onto the same connected component in the host
        else:
            guest_components_to_try = self.guest_component_to_vtxs

        for g_candidate_vtxs in guest_components_to_try:
            for g_candidate_vtx in g_candidate_vtxs:
                if g_candidate_vtx in state.mapping_vtxs:
                    print_debug("skip (already matched)", g_candidate_vtx)
                    continue
                for h_candidate_vtx in state.h_unmatched_vtxs:
                    yield from attempt_match_vtxs(state, g_candidate_vtx, h_candidate_vtx, indent+1)

        if indent == 0:
            print_debug('visited', len(already_visited), 'states total')

# demo time...
if __name__ == "__main__":
    host = Graph()
    host.vtxs = [Vertex(0), Vertex(1), Vertex(2), Vertex(3)]
    host.edges = [
        Edge(host.vtxs[0], host.vtxs[1]),
        Edge(host.vtxs[1], host.vtxs[2]),
        Edge(host.vtxs[2], host.vtxs[0]),
        Edge(host.vtxs[2], host.vtxs[3]),
        Edge(host.vtxs[3], host.vtxs[2]),
    ]

    guest = Graph()
    guest.vtxs = [
        Vertex('v != 3'), # cannot be matched with Vertex(3) - changing this to True, you get 2 morphisms instead of one
        Vertex('True')] # can be matched with any node
    guest.edges = [
        # Look for a simple loop:
        Edge(guest.vtxs[0], guest.vtxs[1]),
        # Edge(guest.vtxs[1], guest.vtxs[0]),
    ]

    m = MatcherVF2(host, guest, lambda g_vtx, h_vtx: eval(g_vtx.value, {}, {'v':h_vtx.value}))
    import time
    durations = 0
    iterations = 1
    print("Patience...")
    for n in range(iterations):
        time_start = time.perf_counter_ns()
        matches = [mm for mm in m.match()]
        time_end = time.perf_counter_ns()
        time_duration = time_end - time_start
        durations += time_duration

    print(f'{iterations} iterations, took {durations/1000000:.3f} ms, {durations/iterations/1000000:.3f} ms per iteration')
    print("found", len(matches), "matches")
    for mm in matches:
        print("match:")
        print(" ", mm.mapping_vtxs)
        print(" ", mm.mapping_edges)

    print("######################")

    host = Graph()
    host.vtxs = [
        Vertex('pony'),   # 1
        Vertex('pony'),   # 3
        Vertex('bear'),
        Vertex('bear'),
    ]
    host.edges = [
        # match:
        Edge(host.vtxs[0], host.vtxs[1]),
        Edge(host.vtxs[1], host.vtxs[0]),
    ]

    guest = Graph()
    guest.vtxs = [
        Vertex('pony'), # 0
        Vertex('pony'), # 1
        Vertex('bear')]
    guest.edges = [
        Edge(guest.vtxs[0], guest.vtxs[1]),
        Edge(guest.vtxs[1], guest.vtxs[0]),
    ]

    m = MatcherVF2(host, guest, lambda g_vtx, h_vtx: g_vtx.value == h_vtx.value)
    import time
    durations = 0
    iterations = 1
    print("Patience...")
    for n in range(iterations):
        time_start = time.perf_counter_ns()
        matches = [mm for mm in m.match()]
        time_end = time.perf_counter_ns()
        time_duration = time_end - time_start
        durations += time_duration

    print(f'{iterations} iterations, took {durations/1000000:.3f} ms, {durations/iterations/1000000:.3f} ms per iteration')
    print("found", len(matches), "matches")
    for mm in matches:
        print("match:")
        print(" ", mm.mapping_vtxs)
        print(" ", mm.mapping_edges)
