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
    random.seed(0)

    graph, pattern = get_random_host_and_guest(
        nr_vtxs        = 10,
        nr_vtx_types   = 0,
        nr_edges       = 20,
        nr_edge_types  = 0,
    )

    # graph, pattern = get_large_host_and_guest()
    # graph, pattern = get_small_host_and_guest()

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