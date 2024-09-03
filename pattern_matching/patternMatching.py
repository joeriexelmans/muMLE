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

import collections
import itertools

class PatternMatching(object):
	"""
	Returns an occurrence of a given pattern from the given Graph
	"""
	def __init__(self, optimize=True):
		# store the type of matching we want to use
		self.optimize		= optimize

	def matchNaive(self, pattern, vertices, edges, pattern_vertices=None):
		"""
		Try to find an occurrence of the pattern in the Graph naively. 
		"""
		# allow call with specific arguments
		if pattern_vertices		== None:
			pattern_vertices	= pattern.vertices

		def visitEdge(pattern_vertices, p_edge, inc, g_edges, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
			"""
			Visit a pattern edge, and try to bind it to a graph edge.
			(If the first fails, try the second, and so on...)
			"""
			for g_edge in g_edges:
				# only reckon the edge if its in edges and not visited
				# (as the graph might be a subgraph of a more complex graph)
				if g_edge not in edges.get(g_edge.type, []) or g_edge in visited_g_edges:
					continue
				if g_edge.type == p_edge.type and g_edge not in visited_g_edges:
					visited_p_edges[p_edge]	= g_edge
					visited_g_edges.add(g_edge)
					if inc:
						p_vertex	= p_edge.src
					else:
						p_vertex	= p_edge.tgt
					if visitVertices(pattern_vertices, p_vertex, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
						return True
					# remove added edges if they lead to no match, retry with others
					del visited_p_edges[p_edge]
					visited_g_edges.remove(g_edge)
			# no edge leads to a possitive match
			return False

		def visitEdges(pattern_vertices, p_edges, inc, g_edges, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
			"""
			Visit all edges of the pattern vertex (edges given as argument).
			We need to try visiting them for all its permutations, as matching
			v -e1-> first and v -e2-> second and v -e3-> third, might not result
			in a matching an occurrence of the pattern, but matching v -e2->
			first and v -e3-> second and v -e1-> third might.
			"""
			def removePrevEdge(visitedEdges, visited_p_edges, visited_g_edges):
				"""
				Undo the binding of the brevious edge, (the current bindinds do
				not lead to an occurrence of the pattern in the graph).
				"""
				for wrong_edge in visitedEdges:
					# remove binding (pattern edge to graph edge)
					wrong_g_edge	= visited_p_edges.get(wrong_edge)
					del visited_p_edges[wrong_edge]
					# remove visited graph edge
					visited_g_edges.remove(wrong_g_edge)

			for it in itertools.permutations(p_edges):
				visitedEdges	= []
				foundallEdges	= True
				for edge in it:
					if visited_p_edges.get(edge) == None:
						if not visitEdge(pattern_vertices, edge, inc, g_edges, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
							# this did not work, so we have to undo all added edges
							# (the current edge is not added, as it failed)
							# we then can try a different permutation
							removePrevEdge(visitedEdges, visited_p_edges, visited_g_edges)
							foundallEdges	= False
							break	# try other order
						# add good visited (we know it succeeded)
						visitedEdges.append(edge)
					else:
						# we visited this pattern edge, and have the coressponding graph edge
						# if it is an incoming pattern edge, we need to make sure that
						# the graph target that is map from the pattern target
						# (of this incoming pattern edge, which has to be bound at this point)
						# has the graph adge as an incoming edge,
						# otherwise the graph is not properly connected
						if inc:
							if not visited_p_edges[edge] in visited_p_vertices[edge.tgt].incoming_edges:
								# did not work
								removePrevEdge(visitedEdges, visited_p_edges, visited_g_edges)
								foundallEdges	= False
								break	# try other order
						else:
							# analog for an outgoing edge
							if not visited_p_edges[edge] in visited_p_vertices[edge.src].outgoing_edges:
								# did not work
								removePrevEdge(visitedEdges, visited_p_edges, visited_g_edges)
								foundallEdges	= False
								break	# try other order

				# all edges are good, look no further
				if foundallEdges:
					break
			return foundallEdges

		def visitVertex(pattern_vertices, p_vertex, g_vertex, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
			"""
			Visit a pattern vertex, and try to bind it to the graph vertex
			(both are given as argument). A binding is successful if all the
			pattern vertex his incoming and outgoing edges can be bound
			(to the graph vertex).
			"""
			if g_vertex in visited_g_vertices:
				return False
			# save visited graph vertex
			visited_g_vertices.add(g_vertex)
			# map pattern vertex to visited graph vertex
			visited_p_vertices[p_vertex]	= g_vertex

			if visitEdges(pattern_vertices, p_vertex.incoming_edges, True, g_vertex.incoming_edges, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
				if visitEdges(pattern_vertices, p_vertex.outgoing_edges, False, g_vertex.outgoing_edges, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
					return True
			# cleanup, remove from visited as this does not lead to
			# an occurrence of the pttern in the graph
			visited_g_vertices.remove(g_vertex)
			del visited_p_vertices[p_vertex]
			return False

		def visitVertices(pattern_vertices, p_vertex, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
			"""
			Visit a pattern vertex and try to bind a graph vertex to it.
			"""
			# if already matched or if it is a vertex not in the pattern_vertices
			# (second is for when you want to match the pattern partionally)
			if visited_p_vertices.get(p_vertex) != None or p_vertex not in pattern_vertices.get(p_vertex.type, set()):
				return True

			# try visiting graph vertices of same type as pattern vertex
			for g_vertex in vertices.get(p_vertex.type, []):
				if g_vertex not in visited_g_vertices:
					if visitVertex(pattern_vertices, p_vertex, g_vertex, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
						return True

			return False

		visited_p_vertices	= {}
		visited_p_edges		= {}
		visited_g_vertices	= set()
		visited_g_edges		= set()

		# for loop is need for when pattern consists of multiple not connected structures
		allVertices	= []
		for _, p_vertices in pattern_vertices.items():
			allVertices.extend(p_vertices)
		foundIt = False
		for it_p_vertices in itertools.permutations(allVertices):
			foundIt = True
			for p_vertex in it_p_vertices:
				if not visitVertices(pattern_vertices, p_vertex, visited_p_vertices, visited_p_edges, visited_g_vertices, visited_g_edges, vertices, edges):
					foundIt = False
					# reset visited
					visited_p_vertices	= {}
					visited_p_edges		= {}
					visited_g_vertices	= set()
					visited_g_edges		= set()
					break
			if foundIt:
				break
		if foundIt:
			return (visited_p_vertices, visited_p_edges)
		else:
			return None

	def createAdjacencyMatrixMap(self, graph, pattern):
		"""
		Return adjacency matrix and the order of the vertices.
		"""
		matrix		= collections.OrderedDict()	# { vertex, (index, [has edge from index to pos?]) }

		# contains all vertices we'll use for the AdjacencyMatrix
		allVertices	= []

		if self.optimize:
			# insert only the vertices from the graph which have a type
			# that is present in the pattern
			for vertex_type, _ in pattern.vertices.items():
				graph_vertices	= graph.vertices.get(vertex_type)
				if graph_vertices	!= None:
					allVertices.extend(graph_vertices)
				else:
					# we will not be able to find the pattern
					# as the pattern contains a vertex of a certain type
					# that is not present in the host graph
					return False
		else:
			# insert all vertices from the graph
			for _, vertices in graph.vertices.items():
				allVertices.extend(vertices)

		# create squared zero matrix
		index	= 0
		for vertex in allVertices:
			matrix[vertex]	= (index, [False] * len(allVertices))
			index	+= 1

		for _, edges in graph.edges.items():
			for edge in edges:
				if self.optimize:
					if edge.tgt not in matrix or edge.src not in matrix:
						# skip adding edge if  the target or source type
						# is not present in the pattern
						# (and therefor not added to the matrix)
						continue
				index	= matrix[edge.tgt][0]
				matrix[edge.src][1][index]	= True

		AM				= []
		vertices_order	= []
		for vertex, row in matrix.items():
			AM.append(row[1])
			vertices_order.append(vertex)

		return AM, vertices_order

	def matchVF2(self, pattern, graph):

		class VF2_Obj(object):
			"""
			Structor for keeping the VF2 data.
			"""
			def __init__(self, len_graph_vertices, len_pattern_vertices):
				# represents if n-the element (h[n] or p[n]) matched
				self.core_graph		= [False]*len_graph_vertices
				self.core_pattern	= [False]*len_pattern_vertices

				# save mapping from pattern to graph
				self.mapping		= {}

				# preference lvl 1
				# ordered set of vertices adjecent to M_graph connected via an outgoing edge
				self.N_out_graph	= [-1]*len_graph_vertices
				# ordered set of vertices adjecent to M_pattern connected via an outgoing edge
				self.N_out_pattern	= [-1]*len_pattern_vertices
				
				# preference lvl 2
				# ordered set of vertices adjecent to M_graph connected via an incoming edge
				self.N_inc_graph	= [-1]*len_graph_vertices
				# ordered set of vertices adjecent to M_pattern connected via an incoming edge
				self.N_inc_pattern	= [-1]*len_pattern_vertices

				# preference lvl 3
				# not in the above

		def findM(H, P, h, p, VF2_obj, index_M=0):
			"""
			Find an isomorphic mapping for the vertices of P to H.
			This mapping is represented by a matrix M if,
			and only if M(MH)^T = P^T.

			This operates in a simular way as Ullmann. Ullmann has a predefind
			order for  matching (sorted on most edges first). VF2's order is to
			first try to match the adjacency vertices connected via outgoing
			edges, then thos connected via incoming edges and then those that
			not connected to the currently mathed vertices.
			"""
			def addOutNeighbours(neighbours, N, index_M):
				"""
				Given outgoing neighbours (a row from an adjacency matrix), 
				label them as added by saving when they got added (index_M
				represents this, otherwise it is -1)
				"""
				for neighbour_index in range(0, len(neighbours)):
					if neighbours[neighbour_index]:
						if N[neighbour_index]	== -1:
							N[neighbour_index]	= index_M

			def addIncNeighbours(G, j, N, index_M):
				"""
				Given the adjacency matrix, and the colum j, representing that 
				we want to add the incoming edges to vertex j,
				label them as added by saving when they got added (index_M
				represents this, otherwise it is -1)
				"""
				for i in range(0, len(G)):
					if G[i][j]:
						if N[i] == -1:
							N[i]	= index_M

			def delNeighbours(N, index_M):
				"""
				Remove neighbours that where added at index_M.
				If we call this function, we are backtracking and we want to
				remove the added neighbours from the just tried matching (n, m)
				pair (whiched failed). 
				"""
				for n in range(0, len(N)):
					if N[n] == index_M:
						N[n]	= -1

			def feasibilityTest(H, P, h, p, VF2_obj, n, m):
				"""
				Examine all the nodes connected to n and m; if such nodes are
				in the current partial mapping, check if each branch from or to
				n has a corresponding branch from or to m and vice versa.

				If the nodes and the branches of the graphs being matched also
				carry semantic attributes, another condition must also hold for
				F(s, n, m) to be true; namely the attributes of the nodes and of
				the branches being paired must be compatible.

				Another pruning step is to check if the nr of ext_edges between
				the matched_vertices from the pattern and its adjecent vertices
				are less than or equal to the nr of ext_edges between
				matched_vertices from the graph and its adjecent vertices.

				And if the nr of ext_edges between those adjecent vertices from
				the pattern and the not connected vertices are less than or
				equal to the nr of ext_edges between those adjecent vertices from
				the graph and its adjecent vertices.
				"""
				# Get all neighbours from graph node n and pattern node m
				# (including n and m)
				neighbours_graph				= {}
				neighbours_graph[h[n].type]		= set([h[n]])

				neighbours_pattern				= {}
				neighbours_pattern[p[m].type]	= set([p[m]])

				# add all neihgbours of pattern vertex m
				for i in range(0, len(P)):	# P is a nxn-matrix
					if (P[m][i] or P[i][m])  and VF2_obj.core_pattern[i]:
						neighbours_pattern.setdefault(p[i].type, set()).add(p[i])

				# add all neihgbours of graph vertex n
				for i in range(0, len(H)):	# P is a nxn-matrix
					if (H[n][i] or H[i][n])  and VF2_obj.core_graph[i]:
						neighbours_graph.setdefault(h[i].type, set()).add(h[i])

				# take a coding shortcut,
				# use self.matchNaive function to see if it is feasable.
				# this way, we immidiatly test the semantic attributes
				if not self.matchNaive(pattern, pattern_vertices=neighbours_pattern, vertices=neighbours_graph, edges=graph.edges):
					return False

				# count ext_edges from core_graph to a adjecent vertices and
				# cuotn ext_edges for adjecent vertices and not matched vertices
				# connected via the ext_edges
				ext_edges_graph_ca	= 0
				ext_edges_graph_an	= 0
				# for all core vertices
				for x in range(0, len(VF2_obj.core_graph)):
					# for all its neighbours
					for y in range(0, len(H)):
						if H[x][y]:
							# if it is a neighbor and not yet matched
							if (VF2_obj.N_out_graph[y] != -1 or VF2_obj.N_inc_graph[y] != -1) and VF2_obj.core_graph[y]:
								# if we matched it
								if VF2_obj.core_graph[x] != -1:
									ext_edges_graph_ca	+= 1
								else:
									ext_edges_graph_an	+= 1

				# count ext_edges from core_pattern to a adjecent vertices
				# connected via the ext_edges
				ext_edges_pattern_ca	= 0
				ext_edges_pattern_an	= 0
				# for all core vertices
				for x in range(0, len(VF2_obj.core_pattern)):
					# for all its neighbours
					for y in range(0, len(P)):
						if P[x][y]:
							# if it is a neighbor and not yet matched
							if (VF2_obj.N_out_pattern[y] != -1 or VF2_obj.N_inc_pattern[y] != -1) and VF2_obj.core_pattern[y]:
								# if we matched it
								if VF2_obj.core_pattern[x] != -1:
									ext_edges_pattern_ca	+= 1
								else:
									ext_edges_pattern_an	+= 1

				# The nr of ext_edges between matched_vertices from the pattern
				# and its adjecent vertices must be less than or equal to the nr
				# of ext_edges between matched_vertices from the graph and its
				# adjecent vertices, otherwise we wont find an occurrence
				if ext_edges_pattern_ca > ext_edges_graph_ca:
					return False

				# The nr of ext_edges between those adjancent vertices from the
				# pattern and its not connected vertices must be less than or
				# equal to the nr of ext_edges between those adjacent vertices
				# from the graph and its not connected vertices,
				# otherwise we wont find an occurrence
				if ext_edges_pattern_an > ext_edges_graph_an:
					return False

				return True

			def matchPhase(H, P, h, p, index_M, VF2_obj, n, m):
				"""
				The matching fase of the VF2 algorithm. If the chosen n, m pair
				passes the feasibilityTest, the pair gets added and we start
				to search for the next matching pair.
				"""
				# all candidate pair (n, m) represent graph x pattern

				candidate = frozenset(itertools.chain(
					((i, j) for i,j in VF2_obj.mapping.items()),
					# ((self.reverseMapH[i], self.reverseMapP[j]) for i,j in VF2_obj.mapping.items()),
					[(h[n],p[m])],
				))

				if candidate in self.alreadyVisited:
				# print(self.indent*"  ", "candidate:", candidate)
				# for match in self.alreadyVisited.get(index_M, []):
					# if match == candidate:
						return False # already visited this (partial) match -> skip


				if feasibilityTest(H, P, h, p, VF2_obj, n, m):
					print(self.indent*"  ","adding to match:", n, "->", m)
					# adapt VF2_obj
					VF2_obj.core_graph[n]	= True
					VF2_obj.core_pattern[m]	= True
					VF2_obj.mapping[h[n]]	= p[m]
					addOutNeighbours(H[n], VF2_obj.N_out_graph, index_M)
					addIncNeighbours(H, n, VF2_obj.N_inc_graph, index_M)
					addOutNeighbours(P[m], VF2_obj.N_out_pattern, index_M)
					addIncNeighbours(P, m, VF2_obj.N_inc_pattern, index_M)

					if index_M > 0:
						# remember our partial match (shallow copy) so we don't visit it again
						self.alreadyVisited.add(frozenset([ (i, j) for i,j in VF2_obj.mapping.items()]))
						# self.alreadyVisited.setdefault(index_M, set()).add(frozenset([ (self.reverseMapH[i], self.reverseMapP[j]) for i,j in VF2_obj.mapping.items()]))
						# print(self.alreadyVisited)

					self.indent += 1
					matched = yield from findM(H, P, h, p, VF2_obj, index_M + 1)
					if matched:
						# return True
						# print(self.indent*"  ","found match", len(self.results), ", continuing...")
						pass
					self.indent -= 1

					if True:
					# else:
						print(self.indent*"  ","backtracking... remove", n, "->", m)

						# else, backtrack, adapt VF2_obj
						VF2_obj.core_graph[n]	= False
						VF2_obj.core_pattern[m]	= False
						del VF2_obj.mapping[h[n]]
						delNeighbours(VF2_obj.N_out_graph, index_M)
						delNeighbours(VF2_obj.N_inc_graph, index_M)
						delNeighbours(VF2_obj.N_out_pattern, index_M)
						delNeighbours(VF2_obj.N_inc_pattern, index_M)

				return False

			def preferred(H, P, h, p, index_M, VF2_obj, N_graph, N_pattern):
				"""
				Try to match the adjacency vertices connected via outgoing
				or incoming edges. (Depending on what is given for N_graph and
				N_pattern.)
				"""
				for n in range(0, len(N_graph)):
					# skip graph vertices that are not in VF2_obj.N_out_graph
					# (or already matched)
					if N_graph[n] == -1 or VF2_obj.core_graph[n]:
						# print(self.indent*"  ","    skipping")
						continue
					print(self.indent*"  ","  n:", n)
					for m in range(0, len(N_pattern)):
						# skip graph vertices that are not in VF2_obj.N_out_pattern
						# (or already matched)
						if N_pattern[m] == -1 or VF2_obj.core_pattern[m]:
							continue
						print(self.indent*"  ","  m:", m)
						matched = yield from matchPhase(H, P, h, p, index_M, VF2_obj, n, m)
						if matched:
							return True

				return False

			def leastPreferred(H, P, h, p, index_M, VF2_obj):
				"""
				Try to match the vertices that are not connected to the curretly
				matched vertices.
				"""
				for n in range(0, len(VF2_obj.N_out_graph)):
					# skip vertices that are connected to the graph 
					# (or already matched)
					if not (VF2_obj.N_out_graph[n] == -1 and VF2_obj.N_inc_graph[n] == -1) or VF2_obj.core_graph[n]:
						# print(self.indent*"  ","    skipping")
						continue
					print("  n:", n)
					for m in range(0, len(VF2_obj.N_out_pattern)):
						# skip vertices that are connected to the graph 
						# (or already matched)
						if not (VF2_obj.N_out_pattern[m] == -1 and VF2_obj.N_inc_pattern[m] == -1) or VF2_obj.core_pattern[m]:
							# print(self.indent*"  ","      skipping")
							continue
						print(self.indent*"  ","    m:", m)
						matched = yield from matchPhase(H, P, h, p, index_M, VF2_obj, n, m)
						if matched:
							return True

				return False

			print(self.indent*"  ","index_M:", index_M)

			# We are at the end, we found an candidate.
			if index_M == len(p):
				print(self.indent*"  ","end...")
				bound_graph_vertices	= {}
				for vertex_bound, _ in VF2_obj.mapping.items():
					bound_graph_vertices.setdefault(vertex_bound.type, set()).add(vertex_bound)

				result	= self.matchNaive(pattern, vertices=bound_graph_vertices, edges=graph.edges)
				if result != None:
					yield result
				return result != None

			if index_M > 0:
				# try the candidates is the preffered order
				# first try the adjacent vertices connected via the outgoing edges.
				print(self.indent*"  ","preferred L1")
				matched = yield from preferred(H, P, h, p, index_M, VF2_obj, VF2_obj.N_out_graph, VF2_obj.N_out_pattern)
				if matched:
					return True

				print(self.indent*"  ","preferred L2")
				# then try the adjacent vertices connected via the incoming edges.
				matched = yield from preferred(H, P, h, p, index_M, VF2_obj, VF2_obj.N_inc_graph, VF2_obj.N_inc_pattern)
				if matched:
					return True

			print(self.indent*"  ","leastPreferred")
			# and lastly, try the vertices not connected to the currently matched vertices
			matched = yield from leastPreferred(H, P, h, p, index_M, VF2_obj)
			if matched:
				return True

			return False

		# create adjecency matrix of the graph
		H, h	= self.createAdjacencyMatrixMap(graph, pattern)
		# create adjecency matrix of the pattern
		P, p	= self.createAdjacencyMatrixMap(pattern, pattern)

		VF2_obj	= VF2_Obj(len(h), len(p))

		# Only for debugging:
		self.indent = 0
		self.reverseMapH = { h[i] : i for i in range(len(h))}
		self.reverseMapP = { p[i] : i for i in range(len(p))}

		# Set of partial matches already explored - prevents us from producing the same match multiple times
		# Encoded as a mapping from match size to the partial match
		self.alreadyVisited = set()

		yield from findM(H, P, h, p, VF2_obj)
