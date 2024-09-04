import itertools

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
    def __init__(self, src: Vertex, tgt: Vertex):
        self.src = src
        self.tgt = tgt
        self.src.outgoing.append(self)
        self.tgt.incoming.append(self)

    def __repr__(self):
        return f"E({self.src}->{self.tgt})"

class MatcherState:
    def __init__(self):
        self.mapping_vtxs = {} # guest -> host
        self.mapping_edges = {} # guest -> host

        self.r_mapping_vtxs = {} # host -> guest
        self.r_mapping_edges = {} # host -> guest

        self.h_unmatched_vtxs = []
        self.g_unmatched_vtxs = []

        # the most recently added pair of (guest,host) vertices
        # will always try to grow mapping via outgoing/incoming edges of this pair before attempting other non-connected vertices
        self.boundary = None

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


class MatcherVF2:
    # Guest is the pattern
    def __init__(self, host, guest, compare_fn):
        self.host = host
        self.guest = guest
        self.compare_fn = compare_fn

    def match(self, state = None, already_visited = set(), indent=0):
        print("  "*indent, "match")
        if state == None:
            state = MatcherState()
            state.h_unmatched_vtxs = self.host.vtxs
            state.g_unmatched_vtxs = self.guest.vtxs

        def visit_for_first_time(state):
            hashable_state = state.make_hashable()
            if hashable_state in already_visited:
                print("  "*indent, 'S K I P  -  A L R E A D Y   V I S I T E D   S T A T E')
                return False
            already_visited.add(hashable_state)
            # print('visisted', len(already_visited), 'states')
            return True


        if len(state.mapping_edges) == len(self.guest.edges):
            print("  "*indent, "GOT MATCH:")
            print("  "*indent, " ", state.mapping_vtxs)
            print("  "*indent, " ", state.mapping_edges)
            yield state
            return

        def attempt_grow(direction, indent):
            print("  "*indent, 'attempt_grow', direction)
            if state.boundary != None:
                g_vtx, h_vtx = state.boundary
                for g_candidate_edge in getattr(g_vtx, direction):
                    # print("  "*indent, g_candidate_edge)
                    if g_candidate_edge in state.mapping_edges:
                        continue # skip already matched guest edge
                    g_candidate_vtx = g_candidate_edge.tgt
                    for h_candidate_edge in getattr(h_vtx, direction):
                        if h_candidate_edge in state.r_mapping_edges:
                            continue # skip already matched host edge
                        h_candidate_vtx = h_candidate_edge.tgt
                        new_state = state.grow_edge(h_candidate_edge, g_candidate_edge)
                        if visit_for_first_time(new_state):
                            print("  "*indent, 'grow edge', g_candidate_edge, ':', h_candidate_edge)
                            yield from attempt_match_vtxs(
                                new_state,
                                g_candidate_vtx,
                                h_candidate_vtx,
                                indent+1)

        def attempt_match_vtxs(state, g_candidate_vtx, h_candidate_vtx, indent):
            # It seems faster (benchmarked) to generate the new_state, even if we still have to check if it's a valid (partial) match, so we can put it in already_visited
            new_state = state.grow_vtx(
                h_candidate_vtx,
                g_candidate_vtx)
            if visit_for_first_time(new_state):
                print("  "*indent, 'attempt_match_vtxs')
                if h_candidate_vtx in state.r_mapping_vtxs:
                    if state.r_mapping_vtxs[h_candidate_vtx] != g_candidate_vtx:
                        return # host vtx is already mapped but doesn't match guest vtx
                g_outdegree = len(g_candidate_vtx.outgoing)
                h_outdegree = len(h_candidate_vtx.outgoing)
                if g_outdegree > h_outdegree:
                    return
                g_indegree = len(g_candidate_vtx.incoming)
                h_indegree = len(h_candidate_vtx.incoming)
                if g_indegree > h_indegree:
                    return
                if not self.compare_fn(h_candidate_vtx.value, g_candidate_vtx.value):
                    return
                print("  "*indent, 'grow vtx', g_candidate_vtx, ':', h_candidate_vtx)
                yield from self.match(new_state, already_visited, indent+1)

        print("  "*indent, 'preferred...')
        yield from attempt_grow('outgoing', indent+1)
        yield from attempt_grow('incoming', indent+1)

        print("  "*indent, 'least preferred...')
        for g_candidate_vtx in state.g_unmatched_vtxs:
            for h_candidate_vtx in state.h_unmatched_vtxs:
                yield from attempt_match_vtxs(state, g_candidate_vtx, h_candidate_vtx, indent+1)

        if indent == 0:
            print('visited', len(already_visited), 'states total')

host = Graph()
host.vtxs = [Vertex(0), Vertex(1), Vertex(2)]
host.edges = [
    Edge(host.vtxs[0], host.vtxs[1]),
    Edge(host.vtxs[1], host.vtxs[2]),
    Edge(host.vtxs[2], host.vtxs[0]),
]

guest = Graph()
guest.vtxs = [Vertex('src'), Vertex('tgt')]
guest.edges = [
    Edge(guest.vtxs[0], guest.vtxs[1]),
]

m = MatcherVF2(host, guest, lambda hv, gv: True)
import time
durations = 0
for n in range(100000):
    time_start = time.perf_counter_ns()
    matches = [mm for mm in m.match()]
    print("found", len(matches), "matches")
    time_end = time.perf_counter_ns()
    time_duration = time_end - time_start
    durations += time_duration

print(f'Took {durations/1000000} ms')
for mm in matches:
    print("match:")
    print(" ", mm.mapping_vtxs)
    print(" ", mm.mapping_edges)