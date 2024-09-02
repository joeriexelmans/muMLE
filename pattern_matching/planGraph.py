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

from searchGraph import *
from enum import *

# Enum for all primitive operation types
# note: inc represent primitive operation in (as in is a reserved keyword in python)
PRIM_OP	= Enum(['lkp', 'inc', 'out', 'src', 'tgt'])

class PlanGraph(object):
	"""
	Holds the PlanGraph for a pattern.
	Can create the search plan of the pattern for a given SearchGraph.
	"""
	def __init__(self, pattern):
		if not isinstance(pattern, Graph):
			raise TypeError('PlanGraph expects the pattern to be a Graph')
		# member variables:
		self.vertices	= []	# will not be searched in
		self.edges		= []	# will not be searched in

		# representation map, maps vertex from pattern to element from PlanGraph
		# (no need for edges)
		repr_map		= {}

		# 1.1: for every vertex in the pattern graph,
		# create a vertex representing the pattern element
		for str_type, vertices in pattern.vertices.items():
			for vertex in vertices:
				# we only need to know the type of the vertex
				plan_vertex				= Vertex(str_type)
				# and we need to know that is was a vertex
				plan_vertex.is_vertex	= True
				# for re-linking the edges, we'll need to map the
				# vertex of the pattern to the plan_vertex
				repr_map[vertex]		= plan_vertex
				# save created plan_vertex
				self.vertices.append(plan_vertex)
		# 1.2: for every edge in the pattern graph,
		# create a vertex representing the pattern elemen
		for str_type, edges in pattern.edges.items():
			for edge in edges:
				# we only need to know the type of the edge
				plan_vertex	= Vertex(edge.type)	
				# and we need to know that is was an edge
				plan_vertex.is_vertex	= False
				# save created plan_vertex
				self.vertices.append(plan_vertex)
				# 4: for every element x from the PlanGraph
				# that represents an edge e in the pattern:
				# 4.1: create an edge labelled tgt from x to the vertex in the PlanGraph
				# representing the target vertex of e in the pattern graph,
				# and a reverted edge labelled in
				# 4.1.1: tgt:
				plan_edge			= Edge(plan_vertex, repr_map[edge.tgt])
				# backup src and tgt (Edmonds might override it)
				plan_edge.orig_src	= plan_edge.src
				plan_edge.orig_tgt	= plan_edge.tgt
				plan_edge.label		= PRIM_OP.tgt
				# link vertices connected to this plan_edge
				plan_edge.src.addOutgoingEdge(plan_edge)
				plan_edge.tgt.addIncomingEdge(plan_edge)
				# tgt and src cost are always 1, we use logaritmic cost,
				# (=> cost = ln(1) = 0.0) so that we do not need to minimaze
				# a product, but can minimize a sum
				# (as ln(c1...ck) = ln(c1) + ... + ln (ck))
				plan_edge.cost		= 0.0
				# backup orig cost, as Edmonds changes cost
				plan_edge.orig_cost	= plan_edge.cost
				# save created edge
				self.edges.append(plan_edge)
				# 4.1.2: in:
				plan_edge			= Edge(repr_map[edge.tgt], plan_vertex)
				# backup src and tgt (Edmonds might override it)
				plan_edge.orig_src	= plan_edge.src
				plan_edge.orig_tgt	= plan_edge.tgt
				plan_edge.label		= PRIM_OP.inc
				# link vertices connected to this plan_edge
				plan_edge.src.addOutgoingEdge(plan_edge)
				plan_edge.tgt.addIncomingEdge(plan_edge)
				# save created edge
				self.edges.append(plan_edge)

				# 4.2: create an edge labelled src from x to the vertex in the PlanGraph
				# representing the source vertex of e in the pattern graph
				# and a reverted edge labelled out
				# 4.2.1: src
				plan_edge			= Edge(plan_vertex, repr_map[edge.src])
				# backup src and tgt (Edmonds might override it)
				plan_edge.orig_src	= plan_edge.src
				plan_edge.orig_tgt	= plan_edge.tgt
				plan_edge.label		= PRIM_OP.src
				# link vertices connected to this plan_edge
				plan_edge.src.addOutgoingEdge(plan_edge)
				plan_edge.tgt.addIncomingEdge(plan_edge)
				# tgt and src cost are always 1, we use logaritmic cost,
				# (=> cost = ln(1) = 0.0) so that we do not need to minimaze
				# a product, but can minimize a sum
				# (as ln(c1...ck) = ln(c1) + ... + ln (ck))
				plan_edge.cost		= 0.0
				# backup orig cost, as Edmonds changes cost
				plan_edge.orig_cost	= plan_edge.cost
				# save created edge
				self.edges.append(plan_edge)				
				# 4.2.2: out
				plan_edge			= Edge(repr_map[edge.src], plan_vertex)
				# backup src and tgt (Edmonds might override it)
				plan_edge.orig_src	= plan_edge.src
				plan_edge.orig_tgt	= plan_edge.tgt
				plan_edge.label		= PRIM_OP.out
				# link vertices connected to this plan_edge
				plan_edge.src.addOutgoingEdge(plan_edge)
				plan_edge.tgt.addIncomingEdge(plan_edge)
				# save created edge
				self.edges.append(plan_edge)
		# 2: create a root vertex
		self.root	= Vertex('root')
		# don't add it to the vertices

		# 3: for each element in the PlanGraph (that is not the root vertex),
		# create an edge from the root to it, and label it lkp
		for vertex in self.vertices:
			plan_edge			= Edge(self.root, vertex)
			# backup src and tgt (Edmonds might override it)
			plan_edge.orig_src	= plan_edge.src
			plan_edge.orig_tgt	= plan_edge.tgt
			plan_edge.label		= PRIM_OP.lkp
			# link vertices connected to this plan_edge
			plan_edge.src.addOutgoingEdge(plan_edge)
			plan_edge.tgt.addIncomingEdge(plan_edge)
			# save created edge
			self.edges.append(plan_edge)

	def updatePlanCost(self, graph):
		"""
		returns True if sucessfully updated cost,
		returns False if a type in the pattern is not in the graph.
		"""
		if not isinstance(graph, SearchGraph):
			raise TypeError('updatePlanCost expects a SearchGraph')
		# update, lkp, in and out (not src and tgt as they are constant)

		for edge in self.edges:
			if edge.label == PRIM_OP.lkp:
				edge.cost	= graph.getCostLkp(edge.tgt.type, edge.tgt.is_vertex)
				if edge.cost == None:
					print('failed lkp')
					return False
			elif edge.label == PRIM_OP.inc:
				# in(v, e), binds an incoming edge e from an already bound vertex v,
				# depends on the number of incoming edges of type e for the vertex type
				edge.cost	= graph.getCostInc(edge.src.type, edge.tgt.type)
				if edge.cost == None:
					print('failed in')
					return False
			elif edge.label == PRIM_OP.out:
				# (analogue for out(v, e))
				edge.cost	= graph.getCostOut(edge.src.type, edge.tgt.type)
				if edge.cost == None:
					print('failed out')
					return False
			# else: ignore src and tgt
			# backup orig cost, as Edmonds changes cost
			edge.orig_cost	= edge.cost
		return True

	def Edmonds(self, searchGraph):
		"""
		Returns the minimum directed spanning tree (MDST)
		for the pattern and the provided graph.
		Returns None if it is impossible to find the pattern in the Graph
		(vertex type of edge type from pattern not in Graph).
		"""
		# update the cost for the PlanGraph
		if not self.updatePlanCost(searchGraph):
			print('type in pattern not found in Graph (in Edmonds)')
			# (returns False if a type in the pattern can not be found in the graph)
			return None
		# Complete Edmonds algorithm has optimization steps:
		# a: remove edges entering the root
		# b: merge parallel edges from same src to same tgt with mim weight
		# we can ignore this as:
		# a: the root does not have incoming edges
		# b: the PlanGraph does not have such paralllel edges

		# 1: for each node v (other than root), find incoming edge with lowest weight
		# insert those 
		pi_v		= {}
		for plan_vertex in self.vertices:
			min_weight	= float('infinity')
			min_edge	= None
			for plan_edge in plan_vertex.incoming_edges:
				if plan_edge.cost < min_weight:
					min_weight	= plan_edge.cost
					min_edge	= plan_edge
			# save plan_vertex and it's minimum incoming edge
			pi_v[plan_vertex]	= min_edge
			if min_edge == None:
				raise RuntimeError('baka: no min_edge found')

		def getCycle(vertex, reverse_graph, visited):
			"""
			Walk from vertex to root, we walk in a reverse order, as each vertex
			only has one incoming edge, so we walk to the source of that incoming
			edge. We stop when we already visited a vertex we walked on.
			In both cases we return None.
			When we visit a vertex from our current path, we return that cycle,
			by first removing its tail.
			"""
			def addToVisited(walked, visited):
				for vertex in walked:
					visited.add(vertex)

			walked			= []	# we could only save it once, but we need order
			current_path	= set()	# and lookup in an array is slower than in set
			# we asume root is in visited (it must be in it)
			while vertex not in visited:
				if vertex in current_path:
					# we found a cycle, the cycle however might look like a: O--,
					# g f e			where we first visited a, then b, c, d,...
					# h   d c b a	k points back to d, completing a cycle,
					# i j k			but c b a is the tail that does not belong
					# in the cycle, removing this is "easy" as we know that
					# we first visited the tail, so they are the first elements
					# in our walked path
					for tail_part in walked:
						if tail_part != vertex:
							current_path.remove(tail_part)
						else:
							break

					addToVisited(walked, visited)
					return current_path
				current_path.add(vertex)
				walked.append(vertex)
				# by definition, an MDST only has one incoming edge per vertex
				# so we follow it upwards
				# vertex <--(minimal edge)-- src
				vertex	= reverse_graph[vertex].src

			# no cycle found (the current path let to a visited vertex)
			addToVisited(walked, visited)	# add walked to visited
			return None

		class VertexGraph(Vertex):
			"""
			Acts as a super vertex, holds a subgraph (that is/was once a cyle).
			Uses for Edmonds contractions step.
			The incoming edges are the edges leading to the vertices in the
			VertexGraph (they exclude edges from a vertex in the cycle to
			another vertex in the cycle).
			Analogue for outgoing edges.
			"""
			def __init__(self, cycle, reverseGraph):
				# Call parent class constructor
				str_type	= ''
				for vertex in cycle:
					str_type += str(vertex.type)
				Vertex.__init__(self, str_type)
				# member variables:
				self.internalMDST		= {}

				minIntWeight	= self.findMinIntWeight(cycle, reverseGraph)
				self.updateMinExtEdge(minIntWeight, reverseGraph)


			def findMinIntWeight(self, cycle, reverseGraph):
				"""
				Find the the smallest cost of the cycle his internal incoming edges.
				(Also save its internalMDST (currently a cycle).)
				(The VertexGraph formed by the cycle will be added to the
				reverseGraph by calling findMinExtEdge.)
				"""
				minIntWeight	= float('infinity')

				cycleEdges	= []
				origTgts	= []
				for cyclePart in cycle:
					cycleEdges.append(reverseGraph[cyclePart])
					origTgts.append(reverseGraph[cyclePart].orig_tgt)

				for vertex in cycle:
					# add incoming edges to this VertexGraph
					for inc_edge in vertex.incoming_edges:
						# edge from within the cycle
						if inc_edge.src in cycle:
							minIntWeight	= min(minIntWeight, inc_edge.cost)
						else:
							# edge from outside the cycle
							self.addIncomingEdge(inc_edge)
					# add outgoing edges to this VertexGraph
					for out_edge in vertex.outgoing_edges:
						if out_edge.tgt not in cycle:
							# edge leaves the cycle
							self.addOutgoingEdge(out_edge)
							# update src to this VertexGraph
							out_edge.src	= self
					# save internal MDST
					min_edge	= reverseGraph[vertex]
					if min_edge.src in cycle:
						self.internalMDST[vertex]	= min_edge
					else:
						raise TypeError('how is this a cycle')

				return minIntWeight

			def updateMinExtEdge(self, minIntWeight, reverseGraph):
				"""
				Modifies all external incoming edges their cost and finds the
				minimum external incoming edge with this modified weight.
				This found edge will break the cycle, update the internalMDST
				from a cycle to an MDST, updates the reverseGraph to include
				the vertexGraph.
				"""
				minExt			= None
				minModWeight	= -float('infinity')

				# Find incoming edge from outside of the circle with minimal
				# modified cost. This edge will break the cycle.
				for inc_edge in self.incoming_edges:
					# An incoming edge (with src from within the cycle), can be
					# from a contracted part of the graph. Assume bc is a
					# contracted part (VertexGraph) a, bc is a newly formed
					# cycle (due to the breaking of the previous cycle bc). bc
					# has at least lkp incoming edges to b and c, but we should
					# not consider the lkp of c to break the cycle.
					# If we want to break a, bc, select plausable edges,
					#  /<--\
					# a     bc   bc's MDST b <-- c
					#  \-->/
					# by looking at their original targets.
					# (if cycle inc_edge.orig_tgt == external inc_edge.orig_tgt)
					if reverseGraph[inc_edge.tgt].orig_tgt == inc_edge.orig_tgt:
						# modify costL cost of inc_edge -
						# (cost of previously choosen minimum edge to cycle vertex - minIntWeight)
						inc_edge.cost	-= (reverseGraph[inc_edge.tgt].cost - minIntWeight)
						if minExt is None or minModWeight > inc_edge.cost:
							# save better edge from outside of the cycle
							minExt			= inc_edge
							minModWeight	= inc_edge.cost

				# Example: a, b is a cycle (we know that there are no other
				# incoming edges to a and/or b, as there is on;y exactly one
				# incoming edge per vertex), and the arow from c to b represents
				# the minExt edge. We will remove the bottem arrow (from a to b)
				#  /<--\			and save the minExt edge in the reverseGraph.
				# a     b <-- c		This breaks the cycle. As the internalMDST
				#  \-->/			saves the intenal MDST, and currently still
				# holds a cycle, we have to remove it from the internalMDST.
				# We have to remove all vertex bindings of the cycle from the
				# reverseGraph (as it is contracted into a single VertexGraph),
				# and store the minExt edge to this VertexGraph in it.
				for int_vertex, _ in self.internalMDST.items():
					del reverseGraph[int_vertex]	# remove cycle from reverseGraph

				del self.internalMDST[minExt.tgt]	# remove/break cycle

				for inc_edge in self.incoming_edges:
					# update inc_edge's target to this VertexGraph
					inc_edge.tgt	= self

				# save minExt edge to this VertexGraph in the reverseGraph
				reverseGraph[self]	= minExt

		while True:
			# 2: find all cycles:
			cycles	= []
			visited	= set([self.root])		# root does not have incoming edges,
			for vertex in list(pi_v.keys()):		# it can not be part of a cycle
				if vertex not in visited:	# getCycle depends on root being in visited
					cycle	= getCycle(vertex, pi_v, visited)
					if cycle != None:
						cycles.append(cycle)

			# 2: if the set of edges {pi(v), v} does not contain any cycles,
			# Then we found our minimum directed spanning tree
			# otherwise, we'll have to resolve the cycles
			if len(cycles) == 0:
				break

			# 3: For each formed cycle:
			# 3a: find internal incoming edge with the smallest cost
			# 3b: modify the cost of each arc which enters the cycle
			# 3c: replace smallert internal edge with the modified edge which has the smallest cost
			for cycle in cycles:
				# Breaks a cycle by:
				# - contracting cycle into VertexGraph
				# - finding the internal incoming edge with the smallest cost
				# - modify the cost of each arc which enters the cycle
				# - replacing the smallest internal edge with the modified edge which has the smallest cost
				# - changing reverseGraph accordingly (removes elements from cycle, ads vertexGraph)
				# (This will find a solution as the graph keeps shrinking with every cycle,
				# in the worst case the same amount as there are vertices, until
				# onlty the root and one vertexGraph remains)
				vertexGraph	= VertexGraph(cycle, pi_v)

		class SortedContainer(object):
			"""
			A container that keeps elemets sorted based on a given sortValue.
			Elements with the same value, will be returned in the order they got inserted.
			"""
			def __init__(self):
				# member variables:
				self.keys	= []	# stores key in sorted order (sorted when pop gets called)
				self.sorted	= {}	# {key, [elems with same key]}

			def add(self, sortValue, element):
				"""
				Adds element with sortValue to the SortedContainer.
				"""
				elems	= self.sorted.get(sortValue)
				if elems == None:
					self.sorted[sortValue]	= [element]
					self.keys.append(sortValue)
				else:
					elems.append(element)

			def pop(self):
				"""
				Sorts the SortedContainer, returns element with smallest sortValue.
				"""
				self.keys.sort()
				elems	= self.sorted[self.keys[0]]
				elem	= elems.pop()
				if len(elems) == 0:
					del self.sorted[self.keys[0]]
					del self.keys[0]
				return elem

			def empty(self):
				"""
				Returns whether or not the sorted container is empty.
				"""
				return (len(self.keys) == 0)

		def createPRIM_OP(edge, inc_cost=True):
			"""
			Helper function to keep argument list short,
			return contracted data for a PRIM_OP.
			"""
			if edge.label == PRIM_OP.inc or edge.label == PRIM_OP.out:
				if inc_cost: # op		# vertex type		# actual edge type
					return (edge.label, edge.orig_src.type, edge.orig_tgt.type, edge.cost)
				else:
					return (edge.label, edge.orig_src.type, edge.orig_tgt.type)
			elif edge.label == PRIM_OP.lkp:
				if inc_cost: # op		# vertex/edge type	# is vertex or edge
					return (edge.label, edge.orig_tgt.type, edge.orig_tgt.is_vertex, edge.cost)
				else:
					return (edge.label, edge.orig_tgt.type, edge.orig_tgt.is_vertex)
			else:	# src, tgt operation
				if inc_cost: # op		# actual edge type
					return (edge.label, edge.orig_src.type, edge.cost)
				else:
					return (edge.label, edge.orig_src.type)

		def flattenReverseGraph(vertex, inc_edge, reverseGraph):
			"""
			Flattens the reverseGraph, so that the vertexGraph node can get
			processed to create a forwardGraph.
			"""
			if not isinstance(vertex, VertexGraph):
				reverseGraph[vertex]	= inc_edge
			else:
				reverseGraph[inc_edge.orig_tgt]	= inc_edge
				for vg, eg in inc_edge.tgt.internalMDST.items():
					flattenReverseGraph(vg, eg, reverseGraph)
			if isinstance(inc_edge.src, VertexGraph):
				for vg, eg in inc_edge.src.internalMDST.items():
					flattenReverseGraph(vg, eg, reverseGraph)

		def createForwardGraph(vertex, inc_edge, forwardGraph):
			"""
			Create a forwardGraph, keeping in mind that their can be vertexGraph
			in the reverseGraph.
			"""
			if not isinstance(vertex, VertexGraph):
				forwardGraph.setdefault(inc_edge.orig_src, []).append(inc_edge)
			else:
				forwardGraph.setdefault(inc_edge.orig_src, []).append(inc_edge)
				for vg, eg in vertex.internalMDST.items():
					createForwardGraph(vg, eg, forwardGraph)

		MDST	= []
		# pi_v contains {vertex, incoming_edge}
		# we want to start from root and follow the outgoing edges
		# so we have to build the forwardGraph graph for pi_v
		# (Except for the root (has 0), each vertex has exactly one incoming edge,
		# but might have multiple outgoing edges)
		forwardGraph	= {}	# {vertex, [outgoing edge 1, ... ] }
		reverseGraph	= {}

		# flatten reverseGraph (for the vertexGraph elements)
		for v, e in pi_v.items():
			flattenReverseGraph(v, e, reverseGraph)

		# create the forwardGraph
		for vertex, edge in reverseGraph.items():
			createForwardGraph(vertex, edge, forwardGraph)

		# create the MDST in a best first manner (lowest value first)
		current		= SortedContainer()		# allows easy walking true tree
		for edge in forwardGraph[self.root]:
			current.add(edge.orig_cost, edge)	# use orig cost, not modified
		while current.empty() != True:
			p_op	= current.pop()				# p_op contains an outgoing edge
			MDST.append(createPRIM_OP(p_op))
			for edge in forwardGraph.get(p_op.orig_tgt, []):
				current.add(edge.orig_cost, edge)
		return MDST