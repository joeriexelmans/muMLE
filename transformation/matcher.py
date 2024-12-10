from api.cd import CDAPI
from api.od import ODAPI, bind_api_readonly
from util.eval import exec_then_eval
from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD
from services import od as services_od
from transformation.vf2 import Graph, Edge, Vertex, MatcherVF2
from transformation import ramify
import itertools
import re
import functools

from util.timer import Timer, counted

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
def model_to_graph(state: State, model: UUID, metamodel: UUID,
    _filter=lambda node: True, prefix=""):
    # with Timer("model_to_graph"):
        od = services_od.OD(model, metamodel, state)
        scd = SCD(model, state)
        scd_mm = SCD(metamodel, state)

        bottom = Bottom(state)

        graph = Graph()

        mvs_edges = []
        modelrefs = {}
        names = {}

        def to_vtx(el, name):
            # print("name:", name)
            if bottom.is_edge(el):
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
        uuid_to_vtx = { node: to_vtx(node, prefix+key) for key in bottom.read_keys(model) for node in bottom.read_outgoing_elements(model, key) if _filter(node) }
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
            vtx.modelref = (ref_m, ref_mm)

        def add_types(node):
            vtx = uuid_to_vtx[node]
            type_node, = bottom.read_outgoing_elements(node, "Morphism")
            # Put the type straight into the Vertex-object
            # The benefit is that our Vertex-matching callback can then be coded cleverly, look at the types first, resulting in better performance
            vtx.typ = type_node

        # Add typing information for:
        #   - classes
        #   - attributes
        #   - associations
        for class_name, class_node in scd_mm.get_classes().items():
            objects = scd.get_typed_by(class_node)
            for obj_name, obj_node in objects.items():
                if _filter(obj_node):
                    add_types(obj_node)
            for attr_name, attr_node in scd_mm.get_attributes(class_name).items():
                attrs = scd.get_typed_by(attr_node)
                for slot_name, slot_node in attrs.items():
                    if _filter(slot_node):
                        add_types(slot_node)
        for assoc_name, assoc_node in scd_mm.get_associations().items():
            objects = scd.get_typed_by(assoc_node)
            for link_name, link_node in objects.items():
                if _filter(link_node):
                    add_types(link_node)

        return names, graph

class _No_Matched(Exception):
    pass
def _cannot_call_matched(_):
    raise _No_Matched()

# This function returns a Generator of matches.
# The idea is that the user can iterate over the match set, lazily generating it: if only interested in the first match, the entire match set doesn't have to be generated.
def match_od(state,
    host_m, # the host graph, in which to search for matches
    host_mm, # meta-model of the host graph
    pattern_m, # the pattern to look for
    pattern_mm, # the meta-model of the pattern (typically the RAMified version of host_mm)
    pivot={}, # optional: a partial match (restricts possible matches, and speeds up the match process)
    eval_context={}, # optional: additional variables, functions, ... to be available while evaluating condition-code in the pattern. Will be available as global variables in the condition-code.
):
    bottom = Bottom(state)

    # compute subtype relations and such:
    cdapi = CDAPI(state, host_mm)
    odapi = ODAPI(state, host_m, host_mm)
    pattern_odapi = ODAPI(state, pattern_m, pattern_mm)
    pattern_mm_odapi = ODAPI(state, pattern_mm, cdapi.mm)

    # 'globals'-dict used when eval'ing conditions
    bound_api = bind_api_readonly(odapi)
    builtin = {
        **bound_api,
        'matched': _cannot_call_matched,
        'odapi': odapi,
    }
    for key in eval_context:
        if key in builtin:
            print(f"WARNING: custom global '{key}' overrides pre-defined API function. Consider renaming it.")
    eval_globals = {
        **builtin,
        **eval_context,
    }

    # Function object for pattern matching. Decides whether to match host and guest vertices, where guest is a RAMified instance (e.g., the attributes are all strings with Python expressions), and the host is an instance (=object diagram) of the original model (=class diagram)
    class RAMCompare:
        def __init__(self, bottom, host_od):
            self.bottom = bottom
            self.host_od = host_od

            type_model_id = bottom.state.read_dict(bottom.state.read_root(), "SCD")
            self.scd_model = UUID(bottom.state.read_value(type_model_id))

            # constraints need to be checked at the very end, after a complete match is established, because constraint code may refer to matched elements by their name
            self.conditions_to_check = {}

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

            types_ok = cdapi.is_subtype(
                super_type_name=guest_type_name_unramified,
                sub_type_name=host_type_name)

            return types_ok

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
                if not self.match_types(g_vtx.typ, h_vtx.typ):
                    return False

            if hasattr(g_vtx, 'modelref'):
                if not hasattr(h_vtx, 'modelref'):
                    return False

                python_code = services_od.read_primitive_value(self.bottom, g_vtx.node_id, pattern_mm)[0]

                try:
                    # Try to execute code, but the likelyhood of failing is high:
                    #   - the `matched` API function is not yet available
                    #   - incompatible slots may be matched (it is only when their AttributeLinks are matched, that we know the types will be compatible)
                    with Timer(f'EVAL condition {g_vtx.name}'):
                        ok = exec_then_eval(python_code,
                            _globals=eval_globals,
                            _locals={'this': h_vtx.node_id})
                    self.conditions_to_check.pop(g_vtx.name, None)
                    return ok
                except:
                    self.conditions_to_check[g_vtx.name] = python_code
                    return True # to be determined later, if it's actually a match

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

            return True

    # Convert to format understood by matching algorithm
    h_names, host = model_to_graph(state, host_m, host_mm)

    # Only match matchable pattern elements
    # E.g., the 'condition'-attribute that is added to every class, cannot be matched with anything
    def is_matchable(pattern_el):
        pattern_el_name = pattern_odapi.get_name(pattern_el)
        if pattern_odapi.get_type_name(pattern_el) == "GlobalCondition":
            return False
        # Super-cheap and unreliable way of filtering out the 'condition'-attribute, added to every class:
        return ((not pattern_el_name.endswith("condition")
            # as an extra safety measure, if the user defined her own 'condition' attribute, RAMification turned this into 'RAM_condition', and we can detect this
            # of course this breaks if the class name already ended with 'RAM', but let's hope that never happens
            # also, we are assuming the default "RAM_" prefix is used, but the user can change this...
            or pattern_el_name.endswith("RAM_condition"))
        and (
                not pattern_el_name.endswith("name")
                or pattern_el_name.endswith("RAM_name") # same thing here as with the condition, explained above.
            ))

    g_names, guest = model_to_graph(state, pattern_m, pattern_mm,
        _filter=is_matchable)

    # precompute the candidates for every guest vertex:
    guest_to_host_candidate_vtxs = {}
    vtxs_of_host_type = {}

    for g_vtx in guest.vtxs:
        object_node = g_vtx.node_id
        if hasattr(g_vtx, 'typ'):
            orig_class_node = ramify.get_original_type(bottom, g_vtx.typ)
            orig_class_name = odapi.get_name(orig_class_node)
            if orig_class_name in vtxs_of_host_type:
                cands = vtxs_of_host_type[orig_class_name]
            else:
                cands = vtxs_of_host_type[orig_class_name] = len(odapi.get_all_instances(orig_class_name, include_subtypes=True))
        else:
            cands = len(host.vtxs)
        guest_to_host_candidate_vtxs[g_vtx] = cands

    # print(guest_to_host_candidate_vtxs)


    # transform 'pivot' into something VF2 understands
    graph_pivot = {
        g_names[guest_name] : h_names[host_name]
            for guest_name, host_name in pivot.items()
                if guest_name in g_names
    }

    obj_conditions = []
    for class_name, class_node in pattern_mm_odapi.get_all_instances("Class"):
        for obj_name, obj_node in pattern_odapi.get_all_instances(class_name):
            python_code = pattern_odapi.get_slot_value_default(obj_node, "condition", 'True')
            if class_name == "GlobalCondition":
                obj_conditions.append((python_code, None))
            else:
                obj_conditions.append((python_code, obj_name))


    def check_conditions(name_mapping):
        eval_globals = {
            **bound_api,
            # this time, the real 'matched'-function can be used:
            'matched': lambda name: bottom.read_outgoing_elements(host_m, name_mapping[name])[0],
            **eval_context,
        }
        def check(python_code: str, loc):
            return exec_then_eval(python_code, _globals=eval_globals, _locals=loc)

        # Attribute conditions
        for pattern_name, host_name in name_mapping.items():
            try:
                python_code = compare.conditions_to_check[pattern_name]
            except KeyError:
                continue
            host_node = odapi.get(host_name)
            with Timer(f'EVAL condition {pattern_name}'):
                if not check(python_code, {'this': host_node}):
                    return False

        for python_code, pattern_el_name in obj_conditions:
            if pattern_el_name == None:
                # GlobalCondition
                with Timer(f'EVAL all global conditions'):
                    if not check(python_code, {}):
                        return False
            else:
                # object-lvl condition
                host_el_name = name_mapping[pattern_el_name]
                host_node = odapi.get(host_el_name)
                with Timer(f'EVAL local condition {pattern_el_name}'):
                    if not check(python_code, {'this': host_node}):
                        return False
        return True


    compare = RAMCompare(bottom, services_od.OD(host_mm, host_m, state))
    matcher = MatcherVF2(host, guest, compare, guest_to_host_candidate_vtxs)
    for m in matcher.match(graph_pivot):
        # Convert mapping
        name_mapping = {}
        for guest_vtx, host_vtx in m.mapping_vtxs.items():
            if isinstance(guest_vtx, NamedNode) and isinstance(host_vtx, NamedNode):
                name_mapping[guest_vtx.name] = host_vtx.name

        if not check_conditions(name_mapping):
            continue # not a match after all...

        yield name_mapping
