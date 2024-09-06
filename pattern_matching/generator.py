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

import graph
# import numpy as np
import math
import collections
import random

class GraphGenerator(object):
    """
    Generates a random Graph with dv an array containing all vertices (there type),
    de an array containing all edges (their type) and dc_inc an array representing
    the incoming edges (analogue for dc_out)
    """
    def __init__(self, dv, de, dc_inc, dc_out, debug=False):
        if len(de) != len(dc_inc):
            raise ValueError('de and dc_inc should be the same length.')
        if len(de) != len(dc_out):
            raise ValueError('de and dc_out should be the same length.')

        self.dv = dv
        self.de = de
        self.dc_inc = dc_inc
        self.dc_out = dc_out

        # print for debugging, so you know the used values
        if debug:
            print('dv')
            print('[',','.join(map(str,dv)),']')
            print('_____')
            print('de')
            print('[',','.join(map(str,de)),']')
            print('_____')
            print('dc_inc')
            print('[',','.join(map(str,dc_inc)),']')
            print('_____')
            print('dc_out')
            print('[',','.join(map(str,dc_out)),']')
            print('_____')

        self.graph    = graph.Graph()
        self.vertices    = []
        # create all the vertices:
        for v_type in self.dv:
            # v_type represents the type of the vertex
            self.vertices.append(self.graph.addCreateVertex('v' + str(v_type)))
        
        index    = 0
        # create all edges
        for e_type in self.de:
            # e_type represents the type of the edge
            src    = self.vertices[self.dc_out[index]]        # get src vertex
            tgt    = self.vertices[self.dc_inc[index]]        # get tgt vertex
            self.graph.addCreateEdge(src, tgt, 'e' + str(e_type))    # create edge
            index    += 1

    def getRandomGraph(self):
        return self.graph

    def getRandomPattern(self, max_nr_of_v, max_nr_of_e, start=0, debug=False):
        # create pattern
        pattern    = graph.Graph()

        # map from graph to new pattern
        graph_to_pattern    = {}

        # map of possible edges
        # we don't need a dict, but python v2.7 does not have an OrderedSet
        possible_edges    = collections.OrderedDict()

        # set of chosen edges
        chosen_edges    = set()

        # start node from graph
        g_node    = self.vertices[start]
        p_node    = pattern.addCreateVertex(g_node.type)
        # for debuging, print the order in which the pattern gets created and
        # connects it edges
        if debug:
            print('v'+str(id(p_node))+'=pattern.addCreateVertex('+"'"+str(g_node.type)+"'"+')')
        # save corrolation
        graph_to_pattern[g_node]    = p_node

        def insertAllEdges(edges, possible_edges, chosen_edges):
            for edge in edges:
                # if we did not chose the edge
                if edge not in chosen_edges:
                    # if inc_edge not in possible edges, add it with value 1
                    possible_edges[edge]    = None

        def insertEdges(g_vertex, possible_edges, chosen_edges):
            insertAllEdges(g_vertex.incoming_edges, possible_edges, chosen_edges)
            insertAllEdges(g_vertex.outgoing_edges, possible_edges, chosen_edges)

        insertEdges(g_node, possible_edges, chosen_edges)

        while max_nr_of_v > len(graph_to_pattern) and max_nr_of_e > len(chosen_edges):
            candidate    = None
            if len(possible_edges) == 0:
                break
            # get a random number between 0 and len(possible_edges)
            # We us a triangular distribution to approximate the fact that
            # the first element is the longest in the possible_edges and
            # already had the post chance of beeing choosen.
            # (The approximation is because the first few ellements where
            # added in the same itteration, but doing this exact is
            # computationally expensive.)
            if len(possible_edges) == 1:
                randie    = 0
            else:
                randie    = int(round(random.triangular(1, len(possible_edges), len(possible_edges)))) - 1
            candidate    = list(possible_edges.keys())[randie]
            del possible_edges[candidate]
            chosen_edges.add(candidate)

            src    = graph_to_pattern.get(candidate.src)
            tgt    = graph_to_pattern.get(candidate.tgt)
            src_is_new    = True
            if src != None and tgt != None:
                # create edge between source and target
                pattern.addCreateEdge(src, tgt, candidate.type)
                if debug:
                    print('pattern.addCreateEdge('+'v'+str(id(src))+', '+'v'+str(id(tgt))+', '+"'"+str(candidate.type)+"'"+')')
                # skip adding new edges
                continue
            elif src == None:
                # create pattern vertex
                src    = pattern.addCreateVertex(candidate.src.type)
                if debug:
                    print('v'+str(id(src))+'=pattern.addCreateVertex('+"'"+str(candidate.src.type)+"'"+')')
                # map newly created pattern vertex
                graph_to_pattern[candidate.src]    = src
                # create edge between source and target
                pattern.addCreateEdge(src, tgt, candidate.type)
                if debug:
                    print('pattern.addCreateEdge('+'v'+str(id(src))+', '+'v'+str(id(tgt))+', '+"'"+str(candidate.type)+"'"+')')
            elif tgt == None:
                src_is_new    = False
                # create pattern vertex
                tgt    = pattern.addCreateVertex(candidate.tgt.type)
                if debug:
                    print('v'+str(id(tgt))+'=pattern.addCreateVertex('+"'"+str(candidate.tgt.type)+"'"+')')
                # map newly created pattern vertex
                graph_to_pattern[candidate.tgt]    = tgt
                # create edge between source and target
                pattern.addCreateEdge(src, tgt, candidate.type)
                if debug:
                    print('pattern.addCreateEdge('+'v'+str(id(src))+', '+'v'+str(id(tgt))+', '+"'"+str(candidate.type)+"'"+')')
            else:
                raise RuntimeError('Bug: src or tgt of edge should be in out pattern')

            # select the vertex from the chosen edge that was not yet part of the pattern
            if src_is_new:
                new_vertex    = candidate.src
            else:
                new_vertex    = candidate.tgt
            # insert all edges from the new vertex
            insertEdges(new_vertex, possible_edges, chosen_edges)

        return pattern

    def createConstantPattern():
        """
        Use this to create the same pattern over and over again.
        """
        # create pattern
        pattern    = graph.Graph()


        # copy and paste printed pattern from debug output or create a pattern
        # below the following line:
        # ----------------------------------------------------------------------
        v4447242448=pattern.addCreateVertex('v4')
        v4457323088=pattern.addCreateVertex('v6')
        pattern.addCreateEdge(v4447242448, v4457323088, 'e4')
        v4457323216=pattern.addCreateVertex('v8')
        pattern.addCreateEdge(v4457323216, v4447242448, 'e4')
        v4457323344=pattern.addCreateVertex('v7')
        pattern.addCreateEdge(v4457323216, v4457323344, 'e3')
        v4457323472=pattern.addCreateVertex('v7')
        pattern.addCreateEdge(v4457323344, v4457323472, 'e1')

        # ----------------------------------------------------------------------
        return pattern

def get_random_host_and_guest(nr_vtxs, nr_vtx_types, nr_edges, nr_edge_types, pattern_nr_vtxs=3, pattern_nr_edges=15):
    dv      = [random.randint(0, nr_vtx_types) for _ in range(nr_vtxs)]
    de      = [random.randint(0, nr_edge_types) for _ in range(nr_edges)]
    dc_inc    = [random.randint(0, nr_vtxs-1) for _ in range(nr_edges)]
    dc_out    = [random.randint(0, nr_vtxs-1) for _ in range(nr_edges)]
    
    return get_host_and_guest(dv, de, dc_inc, dc_out, pattern_nr_vtxs, pattern_nr_edges)

def get_host_and_guest(dv, de, dc_inc, dc_out, pattern_nr_vtxs=3, pattern_nr_edges=15):
    gg    = GraphGenerator(dv, de, dc_inc, dc_out)
    graph    = gg.getRandomGraph()
    pattern    = gg.getRandomPattern(pattern_nr_vtxs, pattern_nr_edges, debug=False)
    return (graph, pattern)


def get_large_host_and_guest():
    dv        = [ 10,5,4,0,8,6,8,0,4,8,5,5,7,0,10,0,5,6,10,4,0,3,0,8,2,7,5,8,1,0,2,10,0,0,1,6,8,4,7,6,4,2,10,10,6,4,6,0,2,7 ]
    de        = [ 8,10,8,1,6,7,4,3,5,2,0,0,9,6,0,3,8,3,2,7,2,3,10,8,10,8,10,2,5,5,10,6,7,5,1,2,1,2,2,3,7,7,2,1,7,2,9,10,8,1,9,4,1,3,1,1,8,2,2,9,10,9,1,9,4,10,10,10,9,3,5,3,6,6,9,1,2,6,3,2,4,10,9,6,5,6,2,4,3,2,4,10,6,2,8,8,0,5,1,7,3,4,3,8,7,3,0,8,3,3,8,5,10,5,9,3,1,10,3,2,6,3,10,0,5,10,9,10,0,1,4,7,10,3,1,9,1,2,3,7,4,3,7,8,8,4,5,10,1,4 ]
    dc_inc    = [ 0,25,18,47,22,25,16,45,38,25,5,45,15,44,17,46,6,17,35,8,16,29,48,47,25,34,4,20,24,1,47,44,8,25,32,3,16,6,33,21,6,13,41,10,17,25,21,33,31,30,5,4,45,26,16,42,12,25,29,3,32,30,14,26,11,13,7,13,3,43,43,22,48,37,20,28,15,40,19,33,43,16,49,36,11,25,9,42,3,22,16,40,42,44,27,30,1,18,10,35,19,6,9,43,37,38,45,19,41,14,37,45,0,31,29,31,24,20,44,46,8,45,43,3,38,38,35,12,19,45,7,34,20,28,12,17,45,17,35,49,20,21,49,1,35,38,38,36,33,30 ]
    dc_out    = [ 9,2,49,49,37,33,16,21,5,46,4,15,9,6,14,22,16,33,23,21,15,31,37,23,47,3,30,26,35,9,29,21,39,32,22,43,5,9,41,30,31,30,37,33,31,34,23,22,34,26,44,36,38,33,48,5,9,34,13,7,48,41,43,26,26,7,12,6,12,28,22,8,29,22,24,27,16,4,31,41,32,15,19,20,38,0,26,18,43,46,40,17,29,14,34,14,32,17,32,47,16,45,7,4,35,22,42,11,38,2,0,29,4,38,17,44,9,23,5,10,31,17,1,11,16,5,37,27,35,32,45,16,18,1,14,4,42,24,43,31,21,38,6,34,39,46,20,1,38,47 ]
    return get_host_and_guest(dv, de, dc_inc, dc_out)

def get_small_host_and_guest():
    dv = [0, 1, 0, 1, 0]
    de = [0, 0, 0]
    dc_inc = [0, 2, 4]
    dc_out = [1, 3, 3]
    return get_host_and_guest(dv, de, dc_inc, dc_out)

