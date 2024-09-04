# coding: utf-8

"""
Author:        Sten Vercamman
            Univeristy of Antwerp

Example code for paper: Efficient model transformations for novices
url: http://msdl.cs.mcgill.ca/people/hv/teaching/MSBDesign/projects/Sten.Vercammen

The main goal of this code is to give an overview, and an understandable
implementation, of known techniques for pattern matching and solving the
sub-graph homomorphism problem. The presented techniques do not include
performance adaptations/optimizations. It is not optimized to be efficient
but rather for the ease of understanding the workings of the algorithms.
The paper does list some possible extensions/optimizations.

It is intended as a guideline, even for novices, and provides an in-depth look
at the workings behind various techniques for efficient pattern matching.
"""

from generator            import *
from patternMatching    import *

import graphToDot

import random

debug = False

if __name__ == '__main__':
    """
    The main function called when running from the command line.
    """
    nr_of_vertices        = 50
    nr_of_diff_types_v    = 2
    nr_of_edges            = 150
    nr_of_diff_types_e    = 2

    dv      = [random.randint(0, nr_of_diff_types_v) for _ in range(nr_of_vertices)]
    de      = [random.randint(0, nr_of_diff_types_e) for _ in range(nr_of_edges)]
    dc_inc    = [random.randint(0, nr_of_vertices-1) for _ in range(nr_of_edges)]
    dc_out    = [random.randint(0, nr_of_vertices-1) for _ in range(nr_of_edges)]

    # override random graph by copy pasting output from terminal
    # dv        = [ 10,5,4,0,8,6,8,0,4,8,5,5,7,0,10,0,5,6,10,4,0,3,0,8,2,7,5,8,1,0,2,10,0,0,1,6,8,4,7,6,4,2,10,10,6,4,6,0,2,7 ]
    # de        = [ 8,10,8,1,6,7,4,3,5,2,0,0,9,6,0,3,8,3,2,7,2,3,10,8,10,8,10,2,5,5,10,6,7,5,1,2,1,2,2,3,7,7,2,1,7,2,9,10,8,1,9,4,1,3,1,1,8,2,2,9,10,9,1,9,4,10,10,10,9,3,5,3,6,6,9,1,2,6,3,2,4,10,9,6,5,6,2,4,3,2,4,10,6,2,8,8,0,5,1,7,3,4,3,8,7,3,0,8,3,3,8,5,10,5,9,3,1,10,3,2,6,3,10,0,5,10,9,10,0,1,4,7,10,3,1,9,1,2,3,7,4,3,7,8,8,4,5,10,1,4 ]
    # dc_inc    = [ 0,25,18,47,22,25,16,45,38,25,5,45,15,44,17,46,6,17,35,8,16,29,48,47,25,34,4,20,24,1,47,44,8,25,32,3,16,6,33,21,6,13,41,10,17,25,21,33,31,30,5,4,45,26,16,42,12,25,29,3,32,30,14,26,11,13,7,13,3,43,43,22,48,37,20,28,15,40,19,33,43,16,49,36,11,25,9,42,3,22,16,40,42,44,27,30,1,18,10,35,19,6,9,43,37,38,45,19,41,14,37,45,0,31,29,31,24,20,44,46,8,45,43,3,38,38,35,12,19,45,7,34,20,28,12,17,45,17,35,49,20,21,49,1,35,38,38,36,33,30 ]
    # dc_out    = [ 9,2,49,49,37,33,16,21,5,46,4,15,9,6,14,22,16,33,23,21,15,31,37,23,47,3,30,26,35,9,29,21,39,32,22,43,5,9,41,30,31,30,37,33,31,34,23,22,34,26,44,36,38,33,48,5,9,34,13,7,48,41,43,26,26,7,12,6,12,28,22,8,29,22,24,27,16,4,31,41,32,15,19,20,38,0,26,18,43,46,40,17,29,14,34,14,32,17,32,47,16,45,7,4,35,22,42,11,38,2,0,29,4,38,17,44,9,23,5,10,31,17,1,11,16,5,37,27,35,32,45,16,18,1,14,4,42,24,43,31,21,38,6,34,39,46,20,1,38,47 ]

    dv = [0, 1, 0, 1, 0]
    de = [0, 0, 0]
    dc_inc = [0, 2, 4]
    dc_out = [1, 3, 3]
    
    gg    = GraphGenerator(dv, de, dc_inc, dc_out, debug)

    graph    = gg.getRandomGraph()

    print(graph.vertices)
    pattern    = gg.getRandomPattern(3, 15, debug=debug)
    print(pattern.vertices)

    # override random pattern by copy pasting output from terminal to create
    # pattern, paste it in the createConstantPattern function in the generator.py
    # pattern    = gg.createConstantPattern()

    # generate here to know pattern and graph before searching it
    graphToDot.printGraph('randomPattern.dot', pattern)
    graphToDot.printGraph('randomGraph.dot', graph)

    
    #PM    = PatternMatching('naive')
    #PM    = PatternMatching('SP')
    # PM    = PatternMatching('Ullmann')
    PM    = PatternMatching('VF2')
    matches = [m for m in PM.matchVF2(pattern, graph)]
    print("found", len(matches), "matches:", matches)

    # regenerate graph, to show matched pattern
    for i, (v,e) in enumerate(matches):
        graphToDot.printGraph(f'randomGraph-{i}.dot', graph, v, e)

    if debug:
        print(len(v))
        print('___')
        print(v)
        for key, value in v.items():
            print(value.type)
        print(len(e))
        print(e)
        print('___')
        for key, value in e.items():
            print(value.type)