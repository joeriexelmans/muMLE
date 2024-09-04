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

import graph as mg

def printGraph(fileName, graph, matched_v={}, matched_e={}):
    if not isinstance(graph, mg.Graph):
        raise TypeError('Can only print Graph Graphs')

    with open(fileName, 'w') as f:
        f.write('digraph randomGraph {\n\n')
        for str_type, plan_vertices in graph.vertices.items():
            for plan_vertex in plan_vertices:
                vertex_str    = str(id(plan_vertex)) + ' [label="'+str(str_type)+'"'
                if plan_vertex in list(matched_v.values()):
                    vertex_str    += ', style=dashed, style=filled]\n'
                else:
                    vertex_str    += ']\n'
                f.write(vertex_str)
                for out_edge in plan_vertex.outgoing_edges:
                    edge_str    = str(id(plan_vertex)) + ' -> ' + str(id(out_edge.tgt)) + ' [label="'+str(out_edge.type)+'"'
                    if out_edge in list(matched_e.values()):
                        edge_str    += ', style=dashed, penwidth = 4]\n'
                    else:
                        edge_str    += ']\n'
                    f.write(edge_str)
        f.write('\n}')