from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD
from services.od import OD
from pattern_matching.matcher import Graph, Edge, Vertex
from transformation import ramify
import itertools
import re
import functools

from util.timer import Timer

from services.primitives.integer_type import Integer

class _is_edge:
    def __repr__(self):
        return "EDGE"
    def to_json(self):
        return "EDGE"
# just a unique symbol that is only equal to itself
IS_EDGE = _is_edge()

class _is_modelref:
    def __repr__(self):
        return "REF"
    def to_json(self):
        return "REF"
IS_MODELREF = _is_modelref()

class IS_TYPE:
    def __init__(self, type):
        # mvs-node of the type
        self.type = type
    def __repr__(self):
        return f"TYPE({str(self.type)[-4:]})"

class NamedNode(Vertex):
    def __init__(self, value, name):
        super().__init__(value)
        # the name of the node in the context of the model
        # the matcher by default ignores this value
        self.name = name

# MVS-nodes become vertices
class MVSNode(NamedNode):
    def __init__(self, value, node_id, name):
        super().__init__(value, name)
        # useful for debugging
        self.node_id = node_id
    def __repr__(self):
        if self.value == None:
            return f"N({self.name})"
        if isinstance(self.value, str):
            return f"N({self.name}=\"{self.value}\")"
        return f"N({self.name}={self.value})"
        # if isinstance(self.value, str):
        #     return f"N({self.name}=\"{self.value}\",{str(self.node_id)[-4:]})"
        # return f"N({self.name}={self.value},{str(self.node_id)[-4:]})"

# MVS-edges become vertices.
class MVSEdge(NamedNode):
    def __init__(self, node_id, name):
        super().__init__(IS_EDGE, name)
        # useful for debugging
        self.node_id = node_id
    def __repr__(self):
        return f"E({self.name})"
        # return f"E({self.name}{str(self.node_id)[-4:]})"

# dirty way of detecting whether a node is a ModelRef
UUID_REGEX = re.compile(r"[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]")

# Converts an object diagram in MVS state to the pattern matcher graph type
# ModelRefs are flattened
def model_to_graph(state: State, model: UUID, metamodel: UUID, prefix=""):
    with Timer("model_to_graph"):
        od = OD(model, metamodel, state)
        scd = SCD(model, state)
        scd_mm = SCD(metamodel, state)

        bottom = Bottom(state)

        graph = Graph()

        mvs_edges = []
        modelrefs = {}
        # constraints = {}

        def to_vtx(el, name):
            # print("name:", name)
            if bottom.is_edge(el):
                # if filter_constraint:
                #     try:
                #         supposed_obj = bottom.read_edge_source(el)
                #         slot_node = od.get_slot(supposed_obj, "constraint")
                #         if el == slot_node:
                #             # `el` is the constraint-slot
                #             constraints[supposed_obj] = el
                #             return
                #     except:
                #         pass
                mvs_edges.append(el)
                return MVSEdge(el, name)
            # If the value of the el is a ModelRef (only way to detect this is to match a regex - not very clean), then extract it. We'll create a link to the referred model later.
            value = bottom.read_value(el)
            if isinstance(value, str):
                if UUID_REGEX.match(value) != None:
                    # side-effect
                    modelrefs[el] = (UUID(value),name)
                    return MVSNode(IS_MODELREF, el, name)
            return MVSNode(value, el, name)

        # MVS-Nodes become vertices
        uuid_to_vtx = { node: to_vtx(node, prefix+key) for key in bottom.read_keys(model) for node in bottom.read_outgoing_elements(model, key) }
        graph.vtxs = [ vtx for vtx in uuid_to_vtx.values() ]

        # For every MSV-Edge, two edges are created (for src and tgt)
        for mvs_edge in mvs_edges:
            mvs_src = bottom.read_edge_source(mvs_edge)
            if mvs_src in uuid_to_vtx:
                graph.edges.append(Edge(
                    src=uuid_to_vtx[mvs_src],
                    tgt=uuid_to_vtx[mvs_edge],
                    label="outgoing"))
            mvs_tgt = bottom.read_edge_target(mvs_edge)
            if mvs_tgt in uuid_to_vtx:
                graph.edges.append(Edge(
                    src=uuid_to_vtx[mvs_edge],
                    tgt=uuid_to_vtx[mvs_tgt],
                    label="tgt"))


        for node, (ref, name) in modelrefs.items():
            # Get MM of ref'ed model
            type_node, = bottom.read_outgoing_elements(node, "Morphism")
            print("modelref type node:", type_node)

            # Recursively convert ref'ed model to graph
            ref_model = model_to_graph(state, ref, type_node, prefix=name+'/')

            # Flatten and create link to ref'ed model
            graph.vtxs += ref_model.vtxs
            graph.edges += ref_model.edges
            graph.edges.append(Edge(
                src=uuid_to_vtx[node],
                tgt=ref_model.vtxs[0], # which node to link to?? dirty
                label="modelref"))

        def add_types(node):
            type_node, = bottom.read_outgoing_elements(node, "Morphism")

            # Put the type straigt into the Vertex-object
            uuid_to_vtx[node].typ = type_node

            # We used to put the types in separate nodes, but we no longer do this:

            # print('node', node, 'has type', type_node)
            # We create a Vertex storing the type
            # type_vertex = Vertex(value=IS_TYPE(type_node))
            # graph.vtxs.append(type_vertex)
            # type_edge = Edge(
            #     src=uuid_to_vtx[node],
            #     tgt=type_vertex,
            #     label="type")
            # # print(type_edge)
            # graph.edges.append(type_edge)


        # Add typing information for:
        #   - classes
        #   - attributes
        #   - associations
        for class_name, class_node in scd_mm.get_classes().items():
            objects = scd.get_typed_by(class_node)
            # print("typed by:", class_name, objects)
            for obj_name, obj_node in objects.items():
                add_types(obj_node)
            for attr_name, attr_node in scd_mm.get_attributes(class_name).items():
                attrs = scd.get_typed_by(attr_node)
                for slot_name, slot_node in attrs.items():
                    add_types(slot_node)
        for assoc_name, assoc_node in scd_mm.get_associations().items():
            objects = scd.get_typed_by(assoc_node)
            # print("typed by:", assoc_name, objects)
            for link_name, link_node in objects.items():
                add_types(link_node)

        return graph

# Function object for pattern matching. Decides whether to match host and guest vertices, where guest is a RAMified instance (e.g., the attributes are all strings with Python expressions), and the host is an instance (=object diagram) of the original model (=class diagram)
class RAMCompare:
    def __init__(self, bottom, host_od):
        self.bottom = bottom
        self.host_od = host_od

        type_model_id = bottom.state.read_dict(bottom.state.read_root(), "SCD")
        self.scd_model = UUID(bottom.state.read_value(type_model_id))

    def is_subtype_of(self, supposed_subtype: UUID, supposed_supertype: UUID):
        if supposed_subtype == supposed_supertype:
            # reflexive:
            return True

        inheritance_node, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")

        for outgoing in self.bottom.read_outgoing_edges(supposed_subtype):
            if inheritance_node in self.bottom.read_outgoing_elements(outgoing, "Morphism"):
                # 'outgoing' is an inheritance link
                supertype = self.bottom.read_edge_target(outgoing)
                if supertype != supposed_subtype:
                    if self.is_subtype_of(supertype, supposed_supertype):
                        return True

        return False

    def match_types(self, g_vtx_type, h_vtx_type):
        # types only match with their supertypes
        # we assume that 'RAMifies'-traceability links have been created between guest and host types
        try:
            g_vtx_original_type = ramify.get_original_type(self.bottom, g_vtx_type)
        except:
            return False

        return self.is_subtype_of(h_vtx_type, g_vtx_original_type)


    # Memoizing the result of comparison gives a huge performance boost!
    # Especially `is_subtype_of` is very slow, and will be performed many times over on the same pair of nodes during the matching process.
    # Assuming the model is not altered *during* matching, this is safe.
    @functools.cache
    def __call__(self, g_vtx, h_vtx):
        # First check if the types match (if we have type-information)
        if hasattr(g_vtx, 'typ'):
            if not hasattr(h_vtx, 'typ'):
                # if guest has a type, host must have a type
                return False
            return self.match_types(g_vtx.typ, h_vtx.typ)

        # Then, match by value

        if g_vtx.value == None:
            return h_vtx.value == None

        # mvs-edges (which are converted to vertices) only match with mvs-edges
        if g_vtx.value == IS_EDGE:
            return h_vtx.value == IS_EDGE

        if h_vtx.value == IS_EDGE:
            return False

        if g_vtx.value == IS_MODELREF:
            return h_vtx.value == IS_MODELREF

        if h_vtx.value == IS_MODELREF:
            return False

        # print(g_vtx.value, h_vtx.value)
        def get_slot(h_vtx, slot_name: str):
            slot_node = self.host_od.get_slot(h_vtx.node_id, slot_name)
            return slot_node

        def read_int(slot: UUID):
            i = Integer(slot, self.bottom.state)
            return i.read()

        try:
            return eval(g_vtx.value, {}, {
                'v': h_vtx.value,
                'get_slot': functools.partial(get_slot, h_vtx),
                'read_int': read_int,
            })
        except Exception as e:
            return False
