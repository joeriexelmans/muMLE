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
