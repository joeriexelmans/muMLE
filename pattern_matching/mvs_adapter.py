from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD
from pattern_matching.matcher import Graph, Edge, Vertex
import itertools
import re

from util.timer import Timer

class _is_edge:
    def __repr__(self):
        return "EDGE"
# just a unique symbol that is only equal to itself
IS_EDGE = _is_edge()

class IS_TYPE:
    def __init__(self, type):
        # mvs-node of the type
        self.type = type

    def __repr__(self):
        return f"TYPE({str(self.type)[-4:]})"

    # def __eq__(self, other):
    #     if not isinstance(other, IS_TYPE):
    #         return False
    #     return other.type == self.type

    # def __hash__(self):
    #     return self.type.__hash__()


UUID_REGEX = re.compile(r"[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z]-[0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z][0-9a-z]")


# Converts an object/class diagram in MVS state to the pattern matcher graph type
# ModelRefs are flattened
def model_to_graph(state: State, model: UUID):
    with Timer("model_to_graph"):
        bottom = Bottom(state)

        graph = Graph()

        mvs_edges = []
        modelrefs = {}
        def extract_modelref(el):
            value = bottom.read_value(el)
            # If the value of the el is a ModelRef (only way to detect this is to match a regex - not very clean), then extract it. We'll create a link to the referred model later.
            if bottom.is_edge(el):
                mvs_edges.append(el)
                return IS_EDGE
            if isinstance(value, str):
                if UUID_REGEX.match(value) != None:
                    # side-effect
                    modelrefs[el] = UUID(value)
                    return None
            return value

        # MVS-Nodes become vertices
        uuid_to_vtx = { node: Vertex(value=extract_modelref(node)) for node in bottom.read_outgoing_elements(model) }
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
                    src=uuid_to_vtx[mvs_tgt],
                    tgt=uuid_to_vtx[mvs_edge],
                    label="tgt"))


        for node, ref in modelrefs.items():
            # Recursively convert ref'ed model to graph
            ref_model = model_to_graph(state, ref)

            # Flatten and create link to ref'ed model
            graph.vtxs += ref_model.vtxs
            graph.edges += ref_model.edges
            graph.edges.append(Edge(
                src=uuid_to_vtx[node],
                tgt=ref_model.vtxs[0], # which node to link to?? dirty
                label="modelref"))

        def add_types(node):
            type_node, = bottom.read_outgoing_elements(node, "Morphism")
            print('node', node, 'has type', type_node)
            # We create a Vertex storing the type
            type_vertex = Vertex(value=IS_TYPE(type_node))
            graph.vtxs.append(type_vertex)
            type_edge = Edge(
                src=uuid_to_vtx[node],
                tgt=type_vertex,
                label="type")
            print(type_edge)
            graph.edges.append(type_edge)


        # Add typing information of classes, attributes, and associations
        scd = SCD(model, state)
        for name,node in scd.get_classes().items():
            add_types(node)
            for attr_name,attr_node in scd.get_attributes(name):
                add_types(attr_node)
        for _,node in scd.get_associations().items():
            add_types(node)

        return graph

# Function object for pattern matching. Decides whether to match host and guest vertices, where guest is a RAMified instance (e.g., the attributes are all strings with Python expressions), and the host is an instance (=object diagram) of the original model (=class diagram)
class RAMCompare:
    def __init__(self, bottom):
        self.bottom = bottom

        type_model_id = bottom.state.read_dict(bottom.state.read_root(), "SCD")
        self.scd_model = UUID(bottom.state.read_value(type_model_id))

    def is_subtype_of(self, supposed_subtype: UUID, supposed_supertype: UUID):
        inheritance_node, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")

        if supposed_subtype == supposed_supertype:
            # reflexive:
            return True

        for outgoing in self.bottom.read_outgoing_edges(supposed_subtype):
            if inheritance_node in self.bottom.read_outgoing_elements(outgoing, "Morphism"):
                # 'outgoing' is an inheritance link
                supertype = self.bottom.read_edge_target(outgoing)
                if supertype != supposed_subtype:
                    if self.is_subtype_of(supertype, supposed_supertype):
                        return True

        return False

    def __call__(self, g_val, h_val):
        if g_val == None:
            return h_val == None

        # mvs-edges (which are converted to vertices) only match with mvs-edges
        if g_val == IS_EDGE:
            return h_val == IS_EDGE

        if h_val == IS_EDGE:
            return False

        # types only match with their supertypes
        # we assume that 'RAMifies'-traceability links have been created between guest and host types
        # we need these links, because the guest types are different types (RAMified)
        if isinstance(g_val, IS_TYPE):
            if not isinstance(h_val, IS_TYPE):
                return False
            g_val_original_types = self.bottom.read_outgoing_elements(g_val.type, "RAMifies")
            if len(g_val_original_types) > 0:
                result = self.is_subtype_of(h_val.type, g_val_original_types[0])
                return result
            else:
                return False

        if isinstance(h_val, IS_TYPE):
            return False

        # print(g_val, h_val)
        return eval(g_val, {}, {'v': h_val})
