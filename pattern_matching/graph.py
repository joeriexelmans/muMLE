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

class Properties(object):
    """
    Holds all Properties.
    """
    def __init__(self):
        # member variables:
        self.properties    = {}

    def addProperty(self, name, value):
        """
        Adds property (overrides if name already exists).
        """
        self.properties[name]    = value

    def getProperty(self, name):
        """
        Returns property with given name or None if not found.
        """
        return self.properties.get(name)

class Edge(Properties):
    """
    Describes an Edge with source and target Node.
    The Edge can have several properties, like a name, a weight, etc...
    """
    def __init__(self, src, tgt, str_type=None):
        # Call parent class constructor
        Properties.__init__(self)
        # member variables:
        self.src    = src
        self.tgt    = tgt
        self.type    = str_type

class Vertex(Properties):
    """
    Describes a Vertex with incoming, outgoing and undirected (both ways) edges.
    The vertex can have several properties, like a name, a weight, etc...
    """
    def __init__(self, str_type):
        # Call parent class constructor
        Properties.__init__(self)
        # member variables:
        self.incoming_edges    = set()    # undirected edges should be stored both in
        self.outgoing_edges    = set()    # incoming and outgoing edges
        self.type            = str_type

    def addIncomingEdge(self, edge):
        """
        Adds an incoming Edge.
        """
        if not isinstance(edge, Edge):
            raise TypeError('addIncomingEdge without it being an edge')
        self.incoming_edges.add(edge)

    def addOutgoingEdge(self, edge):
        """
        Adds an outgoing Edge.
        """
        if not isinstance(edge, Edge):
            raise TypeError('addOutgoingEdge without it being an edge')
        self.outgoing_edges.add(edge)

    def addUndirectedEdge(self, edge):
        """
        Adds an undirected (or bi-directed) Edge.
        """
        self.addIncomingEdge(edge)
        self.addOutgoingEdge(edge)

class Graph(object):
    """
    Holds a Graph.
    """
    def __init__(self):
        # member variables:
        # redundant type keeping, "needed" for fast iterating over specific type
        self.vertices    = {}    # {type, set(v1, v2, ...)}
        self.edges        = {}    # {type, set(e1, e2, ...)}
        
    def addCreateVertex(self, str_type):
        """
        Creates a Vertex of str_type, stores it and returs it
        (so that properties can be added to it).
        """
        vertex    = Vertex(str_type)
        self.addVertex(vertex)
        return vertex

    def addVertex(self, vertex):
        """
        Stores a Vertex into the Graph.
        """
        if not isinstance(vertex, Vertex):
            raise TypeError('addVertex expects a Vertex')
        # add vertex, but it first creates a new set for the vertex type
        # if the type does not exist in the dictionary
        self.vertices.setdefault(vertex.type, set()).add(vertex)

    def getVerticesOfType(self, str_type):
        """
        Returns all vertices of a specific type,
        Return [] if there are no vertices with the given type
        """
        return self.vertices.get(str_type, [])

    def getEdgesOfType(self, str_type):
        """
        Returns all edges of a specific type,
        Return [] if there are no edges with the given type
        """
        return self.edges.get(str_type, [])

    def addCreateEdge(self, src, tgt, str_type):
        """
        Creates edge of str_type from src to tgt, and returns it,
        so that properties can be added to the edge.
        """
        if not isinstance(src, Vertex):
            raise TypeError('addCreateEdge: src is not a Vertex')
        if not isinstance(tgt, Vertex):
            raise TypeError('addCreateEdge: tgt is not a Vertex')
        edge    = Edge(src, tgt, str_type)
        # link vertices connected to this edge
        edge.src.addOutgoingEdge(edge)
        edge.tgt.addIncomingEdge(edge)
        self.addEdge(edge)
        return edge

    def addEdge(self, edge):
        """
        Stores an Edge into the Graph.
        """
        if not isinstance(edge, Edge):
            raise TypeError('addEdge expects an Edge')
        # add edge, but it first creates a new set for the edge type
        # if the type does not exist in the dictionary
        self.edges.setdefault(edge.type, set()).add(edge)
