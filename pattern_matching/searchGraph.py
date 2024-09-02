# coding: utf-8

"""
Author:		Sten Vercamman
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

from graph import *

import math

class SearchGraph(Graph):
	"""
	A SearchGraph is an extended Graph, it keeps traks of statistics
	for creating the cost model when generating a search plan.
	It stire the amount of edges for each edge.type per vertex.type.
	"""
	def __init__(self, orig=None, deepCopy=False):
		Graph.__init__(self)
		# member variables:
		self.nr_of_inc_edges	= {}	# {vertex_type, {edge_type, nr of incoming edges of edge_type for vertex_type } }
		self.nr_of_out_edges	= {}	# {vertex_type, {edge_type, nr of outgoing edges of edge_type for vertex_type } }

		if orig != None:
			if not (isinstance(orig, Graph) or isinstance(orig, SearchGraph)):
				raise TypeError('Can only create SearchGraph from Graph and SearchGraph types')
			if not deepCopy:
				# copy all memeber elements:
				self.vertices	= orig.vertices	# this is a reference
				self.edges		= orig.edges	# this is a reference
				# udpate the edge counters for each edge
				for _, edges in self.edges.items():
					for edge in edges:
						self.addToEdgeCounters(edge)
			else: # TODO: deepcopy (not really needed)
				pass

	def addCreateEdge(self, src, tgt, str_type):
		"""
		Creates edge of str_type from src to tgt, and returns it,
		so that properties can be added to the edge.
		This also add the Edge to the Edge counters
		"""
		# call parent fucntion, this function is an extention
		edge	= Graph.addCreateEdge(self, src, tgt, str_type)
		self.updateEdgeCounters(edge)
		return edge

	def addToEdgeCounters(self, edge):
		"""
		Add the Edge to the Edge counters.
		"""
		# get {edge.type, counter} for tgt vertex of edge (or create it)
		edge_counters				= self.nr_of_inc_edges.setdefault(edge.tgt.type, {})
		# increase counter of edge.type by 1
		edge_counters[edge.type]	= edge_counters.get(edge.type, 0) + 1
		# get {edge.type, counter} for src vertex of edge (or create it)
		edge_counters				= self.nr_of_out_edges.setdefault(edge.src.type, {})
		# increase counter of edge.type by 1
		edge_counters[edge.type]	= edge_counters.get(edge.type, 0) + 1

	def getCostLkp(self, type, is_vertex):
		"""
		Returns the cost of a lkp primitive operation (of a vertex or edge).
		Returns None if vertex type or edge type not present in Host Graph
		"""
		if is_vertex:
			cost	= len(self.getVerticesOfType(type))
		else:
			cost	= len(self.getEdgesOfType(type))
		if cost == 0:
			return None
		# we use a logaritmic cost
		return math.log(cost)

	def getCostInc(self, vertex_type, edge_type):
		"""
		Returns the cost of an in primitive operation.
		Returns None if vertex_type or edge_type not present in Host Graph
		"""
		cost	= float(self.nr_of_inc_edges.get(vertex_type, {}).get(edge_type))
		if cost != None:
			nr_of_vertices_with_type	= len(self.getVerticesOfType(vertex_type))
			if nr_of_vertices_with_type != 0:
				cost	/= len(self.getVerticesOfType(vertex_type))
				# we use a logaritmic cost
				cost	= math.log(cost)
		return cost

	def getCostOut(self, vertex_type, edge_type):
		"""
		Returns the cost of an out primitive operation.
		Returns None if vertex_type or edge_type not present in Host Graph
		"""
		cost	= float(self.nr_of_out_edges.get(vertex_type, {}).get(edge_type))
		if cost != None:
			nr_of_vertices_with_type	= len(self.getVerticesOfType(vertex_type))
			if nr_of_vertices_with_type != 0:
				cost	/= len(self.getVerticesOfType(vertex_type))
				# we use a logaritmic cost
				cost	= math.log(cost)
		return cost