from api.cd import CDAPI
from api.od import ODAPI, bind_api_readonly
from util.eval import exec_then_eval
from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD
from services import od as services_od
from transformation.matcher.matcher import Graph, Edge, Vertex, MatcherVF2
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

# class IS_TYPE:
#     def __init__(self, type):
#         # mvs-node of the type
#         self.type = type
#     def __repr__(self):
#         return f"TYPE({str(self.type)[-4:]})"

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
    # with Timer("model_to_graph"):
        od = services_od.OD(model, metamodel, state)
        scd = SCD(model, state)
        scd_mm = SCD(metamodel, state)

        bottom = Bottom(state)

        graph = Graph()

        mvs_edges = []
        modelrefs = {}
        # constraints = {}

        names = {}

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
                edge = MVSEdge(el, name)
                names[name] = edge
                return edge
            # If the value of the el is a ModelRef (only way to detect this is to match a regex - not very clean), then extract it. We'll create a link to the referred model later.
            value = bottom.read_value(el)
            if isinstance(value, str):
                if UUID_REGEX.match(value) != None:
                    # side-effect
                    modelrefs[el] = (UUID(value), name)
                    return MVSNode(IS_MODELREF, el, name)
            node = MVSNode(value, el, name)
            names[name] = node
            return node

        # Objects and Links become vertices
        uuid_to_vtx = { node: to_vtx(node, prefix+key) for key in bottom.read_keys(model) for node in bottom.read_outgoing_elements(model, key) }
        graph.vtxs = [ vtx for vtx in uuid_to_vtx.values() ]

        # For every Link, two edges are created (for src and tgt)
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


        for node, (ref_m, name) in modelrefs.items():
            vtx = uuid_to_vtx[node]

            # Get MM of ref'ed model
            ref_mm, = bottom.read_outgoing_elements(node, "Morphism")
            # print("modelref type node:", type_node)

            # Recursively convert ref'ed model to graph
            # ref_graph = model_to_graph(state, ref_m, ref_mm, prefix=name+'/')

            vtx.modelref = (ref_m, ref_mm)

            # We no longer flatten:

            # # Flatten and create link to ref'ed model
            # graph.vtxs += ref_model.vtxs
            # graph.edges += ref_model.edges
            # graph.edges.append(Edge(
            #     src=uuid_to_vtx[node],
            #     tgt=ref_model.vtxs[0], # which node to link to?? dirty
            #     label="modelref"))

        def add_types(node):
            vtx = uuid_to_vtx[node]
            type_node, = bottom.read_outgoing_elements(node, "Morphism")

            # Put the type straight into the Vertex-object
            # The benefit is that our Vertex-matching callback can then be coded cleverly, look at the types first, resulting in better performance
            vtx.typ = type_node

            # The old approach (creating special vertices containing the types), commented out:

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

        return names, graph


def match_od(state, host_m, host_mm, pattern_m, pattern_mm, pivot={}):

    # compute subtype relations and such:
    cdapi = CDAPI(state, host_mm)
    odapi = ODAPI(state, host_m, host_mm)

    # Function object for pattern matching. Decides whether to match host and guest vertices, where guest is a RAMified instance (e.g., the attributes are all strings with Python expressions), and the host is an instance (=object diagram) of the original model (=class diagram)
    class RAMCompare:
        def __init__(self, bottom, host_od):
            self.bottom = bottom
            self.host_od = host_od

            type_model_id = bottom.state.read_dict(bottom.state.read_root(), "SCD")
            self.scd_model = UUID(bottom.state.read_value(type_model_id))

        def match_types(self, g_vtx_type, h_vtx_type):
            # types only match with their supertypes
            # we assume that 'RAMifies'-traceability links have been created between guest and host types
            try:
                g_vtx_unramified_type = ramify.get_original_type(self.bottom, g_vtx_type)
            except:
                return False

            try:
                host_type_name = cdapi.type_model_names[h_vtx_type]
                guest_type_name_unramified = cdapi.type_model_names[g_vtx_unramified_type]
            except KeyError:
                return False

            return cdapi.is_subtype(
                super_type_name=guest_type_name_unramified,
                sub_type_name=host_type_name)

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

            if hasattr(g_vtx, 'modelref'):
                if not hasattr(h_vtx, 'modelref'):
                    return False

                python_code = services_od.read_primitive_value(self.bottom, g_vtx.node_id, pattern_mm)[0]
                return exec_then_eval(python_code,
                    _globals=bind_api_readonly(odapi),
                    _locals={'this': h_vtx.node_id})

                # nested_matches = [m for m in match_od(state, h_ref_m, h_ref_mm, g_ref_m, g_ref_mm)]


                # print('begin recurse')
                # g_ref_m, g_ref_mm = g_vtx.modelref
                # h_ref_m, h_ref_mm = h_vtx.modelref
                # print('nested_matches:', nested_matches)
                # if len(nested_matches) == 0:
                #     return False
                # elif len(nested_matches) == 1:
                #     return True
                # else:
                #     raise Exception("We have a problem: there is more than 1 match in the nested models.")
                # print('end recurse')

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

            # python_code = g_vtx.value
            # try:
            #     return exec_then_eval(python_code,
            #         _globals=bind_api_readonly(odapi),
            #         _locals={'this': h_vtx.node_id})
            # except Exception as e:
            #     print(e)
            #     return False
            return True

    # Convert to format understood by matching algorithm
    h_names, host = model_to_graph(state, host_m, host_mm)
    g_names, guest = model_to_graph(state, pattern_m, pattern_mm)


    graph_pivot = {
        g_names[guest_name] : h_names[host_name]
            for guest_name, host_name in pivot.items()
                if guest_name in g_names
    }

    matcher = MatcherVF2(host, guest, RAMCompare(Bottom(state), services_od.OD(host_mm, host_m, state)))
    for m in matcher.match(graph_pivot):
        # print("\nMATCH:\n", m)
        # Convert mapping
        name_mapping = {}
        for guest_vtx, host_vtx in m.mapping_vtxs.items():
            if isinstance(guest_vtx, NamedNode) and isinstance(host_vtx, NamedNode):
                name_mapping[guest_vtx.name] = host_vtx.name
        yield name_mapping
