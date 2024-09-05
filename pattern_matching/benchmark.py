import time

import matcher as j # joeri's matcher
import graph as sgraph # sten's graph
import patternMatching as s # sten's matcher
import generator

def j_to_s(j):
    s = sgraph.Graph()
    m = {}
    for jv in j.vtxs:
        sv = s.addCreateVertex(jv.value) # value becomes type
        m[jv] = sv
    for je in j.edges:
        s.addCreateEdge(m[je.src], m[je.tgt], "e") # only one type
    return s

def s_to_j(s):
    jg = j.Graph()
    jg.vtxs = [ j.Vertex(typ) for (typ,svs) in s.vertices.items() for sv in svs  ]
    m = { sv : jg.vtxs[i] for svs in s.vertices.values() for i,sv in enumerate(svs) }
    jg.edges = [j.Edge(m[se.src], m[se.tgt]) for ses in s.edges.values() for se in ses ]
    return j


def run_benchmark(jhost, jguest, shost, sguest, expected=None):
    j_durations = 0
    s_durations = 0

    # benchmark Joeri
    m = j.MatcherVF2(host, guest,
        lambda g_val, h_val: g_val == h_val) # all vertices can be matched
    iterations = 50
    print(" Patience (joeri)...")
    for n in range(iterations):
        time_start = time.perf_counter_ns()
        matches = [mm for mm in m.match()]
        time_end = time.perf_counter_ns()
        duration = time_end - time_start
        j_durations += duration
    print(f'  {iterations} iterations, took {j_durations/1000000:.3f} ms, {j_durations/iterations/1000000:.3f} ms per iteration')
    if expected == None:
        print(f"  {len(matches)} matches")
    else:
        if len(matches) == expected:
            print("  correct (probably)")
        else:
            print(f"  WRONG! expected: {expected}, got: {len(matches)}")
    # print([m.mapping_vtxs for m in matches])
    # print([m.mapping_edges for m in matches])

    # benchmark Sten
    m = s.PatternMatching()
    print(" Patience (sten)...")
    for n in range(iterations):
        time_start = time.perf_counter_ns()
        matches = [mm for mm in m.matchVF2(sguest, shost)]
        time_end = time.perf_counter_ns()
        duration = time_end - time_start
        s_durations += duration
    print(f'  {iterations} iterations, took {s_durations/1000000:.3f} ms, {s_durations/iterations/1000000:.3f} ms per iteration')
    if expected == None:
        print(f"  {len(matches)} matches")
    else:
        if len(matches) == expected:
            print("  correct (probably)")
        else:
            print(f"  WRONG! expected: {expected}, got: {len(matches)}")
    # print(matches)

    print(f" joeri is {s_durations/j_durations:.2f} times faster")

if __name__ == "__main__":

    print("\nBENCHMARK: small graph, simple pattern")

    host = j.Graph()
    host.vtxs = [j.Vertex(0), j.Vertex(0), j.Vertex(0), j.Vertex(0)]
    host.edges = [
        j.Edge(host.vtxs[0], host.vtxs[1]),
        j.Edge(host.vtxs[1], host.vtxs[2]),
        j.Edge(host.vtxs[2], host.vtxs[0]),
        j.Edge(host.vtxs[2], host.vtxs[3]),
        j.Edge(host.vtxs[3], host.vtxs[2]),
    ]

    guest = j.Graph()
    guest.vtxs = [
        j.Vertex(0),
        j.Vertex(0)]
    guest.edges = [
        # Look for a simple loop:
        j.Edge(guest.vtxs[0], guest.vtxs[1]),
        j.Edge(guest.vtxs[1], guest.vtxs[0]),
    ]

    # because of the symmetry in our pattern, there will be 2 matches

    run_benchmark(host, guest, j_to_s(host), j_to_s(guest), expected=2)

    #######################################################################

    print("\nBENCHMARK: larger graph, simple pattern")

    host = j.Graph()
    host.vtxs = [
        j.Vertex('triangle'), # 0
        j.Vertex('square'),   # 1
        j.Vertex('square'),   # 2
        j.Vertex('circle'),   # 3
        j.Vertex('circle'),   # 4
        j.Vertex('circle'),   # 5
    ]
    host.edges = [
        # not a match:
        j.Edge(host.vtxs[0], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[0]),

        # will be a match:
        j.Edge(host.vtxs[1], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[1]),

        # noise:
        j.Edge(host.vtxs[1], host.vtxs[2]),

        # will be a match:
        j.Edge(host.vtxs[2], host.vtxs[4]),
        j.Edge(host.vtxs[4], host.vtxs[2]),

        # noise:
        j.Edge(host.vtxs[0], host.vtxs[1]),
        j.Edge(host.vtxs[0], host.vtxs[3]),
        j.Edge(host.vtxs[0], host.vtxs[0]),
        j.Edge(host.vtxs[1], host.vtxs[1]),

        # will be a match:
        j.Edge(host.vtxs[3], host.vtxs[2]),
        j.Edge(host.vtxs[2], host.vtxs[3]),
    ]

    guest = j.Graph()
    guest.vtxs = [
        j.Vertex('square'), # 0
        j.Vertex('circle')] # 1
    guest.edges = [
        j.Edge(guest.vtxs[0], guest.vtxs[1]),
        j.Edge(guest.vtxs[1], guest.vtxs[0]),
    ]

    # should give 3 matches

    run_benchmark(host, guest, j_to_s(host), j_to_s(guest), expected=3)

    #######################################################################

    print("\nBENCHMARK: same as before, but with larger pattern")

    host = j.Graph()
    host.vtxs = [
        j.Vertex('triangle'), # 0
        j.Vertex('square'),   # 1
        j.Vertex('square'),   # 2
        j.Vertex('circle'),   # 3
        j.Vertex('circle'),   # 4
        j.Vertex('circle'),   # 5
    ]
    host.edges = [
        # not a match:
        j.Edge(host.vtxs[0], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[0]),

        # will be a match:
        j.Edge(host.vtxs[1], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[1]),

        # noise:
        j.Edge(host.vtxs[1], host.vtxs[2]),

        # will be a match:
        j.Edge(host.vtxs[2], host.vtxs[4]),
        j.Edge(host.vtxs[4], host.vtxs[2]),

        # noise:
        j.Edge(host.vtxs[0], host.vtxs[1]),
        j.Edge(host.vtxs[0], host.vtxs[3]),
        j.Edge(host.vtxs[0], host.vtxs[0]),
        j.Edge(host.vtxs[1], host.vtxs[1]),

        # will be a match:
        j.Edge(host.vtxs[3], host.vtxs[2]),
        j.Edge(host.vtxs[2], host.vtxs[3]),
    ]

    guest = j.Graph()
    guest.vtxs = [
        j.Vertex('square'), # 0
        j.Vertex('circle'), # 1
        j.Vertex('square')] # 2
    guest.edges = [
        j.Edge(guest.vtxs[0], guest.vtxs[1]),
        j.Edge(guest.vtxs[1], guest.vtxs[0]),
        j.Edge(guest.vtxs[2], guest.vtxs[0]),
    ]

    # this time, only 2 matches

    run_benchmark(host, guest, j_to_s(host), j_to_s(guest), expected=2)

    #######################################################################

    print("\nBENCHMARK: disconnected pattern")

    host = j.Graph()
    host.vtxs = [
        j.Vertex('triangle'), # 0
        j.Vertex('square'),   # 1
        j.Vertex('square'),   # 2
        j.Vertex('circle'),   # 3
        j.Vertex('circle'),   # 4
        j.Vertex('circle'),   # 5
        j.Vertex('bear'),
        j.Vertex('bear'),
    ]
    host.edges = [
        # not a match:
        j.Edge(host.vtxs[0], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[0]),

        # will be a match:
        j.Edge(host.vtxs[1], host.vtxs[5]),
        j.Edge(host.vtxs[5], host.vtxs[1]),

        # noise:
        j.Edge(host.vtxs[1], host.vtxs[2]),

        # will be a match:
        j.Edge(host.vtxs[2], host.vtxs[4]),
        j.Edge(host.vtxs[4], host.vtxs[2]),

        # noise:
        j.Edge(host.vtxs[0], host.vtxs[1]),
        j.Edge(host.vtxs[0], host.vtxs[3]),
        j.Edge(host.vtxs[0], host.vtxs[0]),
        j.Edge(host.vtxs[1], host.vtxs[1]),

        # will be a match:
        j.Edge(host.vtxs[3], host.vtxs[2]),
        j.Edge(host.vtxs[2], host.vtxs[3]),
    ]

    guest = j.Graph()
    guest.vtxs = [
        j.Vertex('square'), # 0
        j.Vertex('circle'), # 1
        j.Vertex('bear')]
    guest.edges = [
        j.Edge(guest.vtxs[0], guest.vtxs[1]),
        j.Edge(guest.vtxs[1], guest.vtxs[0]),
    ]

    # the 'bear' in our pattern can be matched with any of the two bears in the graph, effectively doubling the number of matches

    run_benchmark(host, guest, j_to_s(host), j_to_s(guest), expected=6)

    #######################################################################

    print("\nBENCHMARK: larger graph")

    shost, sguest = generator.get_large_host_and_guest()
    run_benchmark(s_to_j(shost), s_to_j(sguest), shost, sguest)

    #######################################################################

    print("\nBENCHMARK: large random graph")

    import random
    random.seed(0)

    shost, sguest = generator.get_random_host_and_guest(
        nr_vtxs        = 10,
        nr_vtx_types   = 0,
        nr_edges       = 20,
        nr_edge_types  = 0,
    )
    run_benchmark(s_to_j(shost), s_to_j(sguest), shost, sguest)

