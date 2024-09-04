from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD
from framework.conformance import Conformance


def ramify(state: State, model: UUID) -> UUID:

    def print_tree(root, max_depth, depth=0):
        print("  "*depth, "root=", root, "value=", state.read_value(root))
        src,tgt = state.read_edge(root)
        if src != None:
            print("  "*depth, "src...")
            print_tree(src, max_depth, depth+1)
        if tgt != None:
            print("  "*depth, "tgt...")
            print_tree(tgt, max_depth, depth+1)
        for edge in state.read_outgoing(root):
            for edge_label in state.read_outgoing(edge):
                [_,tgt] = state.read_edge(edge_label)
                label = state.read_value(tgt)
                print("  "*depth, " key:", label)
            [_, tgt] = state.read_edge(edge)
            value = state.read_value(tgt)
            if value != None:
                print("  "*depth, " ->", tgt, " (value:", value, ")")
            else:
                print("  "*depth, " ->", tgt)
            if depth < max_depth:
                if isinstance(value, str) and len(value) == 36:
                    i = None
                    try:
                        i = UUID(value)
                    except ValueError as e:
                        # print("invalid UUID:", value)
                        pass
                    if i != None:
                        print_tree(i, max_depth, depth+1)
                print_tree(tgt, max_depth, depth+1)

    bottom = Bottom(state)

    scd_metamodel_id = state.read_dict(state.read_root(), "SCD")
    scd_metamodel = UUID(state.read_value(scd_metamodel_id))

    class_upper_card_node, = bottom.read_outgoing_elements(scd_metamodel, "Class_upper_cardinality")
    src_upper_card_node, = bottom.read_outgoing_elements(scd_metamodel, "Association_source_upper_cardinality")
    tgt_upper_card_node, = bottom.read_outgoing_elements(scd_metamodel, "Association_target_upper_cardinality")
    attr_link_node, = bottom.read_outgoing_elements(scd_metamodel, "AttributeLink")
    attr_link_name_node, = bottom.read_outgoing_elements(scd_metamodel, "AttributeLink_name")
    glob_constr_node, = bottom.read_outgoing_elements(scd_metamodel, "GlobalConstraint")
    inheritance_node, = bottom.read_outgoing_elements(scd_metamodel, "Inheritance")

    string_type_id = state.read_dict(state.read_root(), "String")
    string_type = UUID(state.read_value(string_type_id))

    scd = SCD(model, state)

    # print_tree(model, 2)

    # for el in SCD(scd_metamodel, state).list_elements():
    #     print(el)

    def find_outgoing_typed_by(src: UUID, type_node: UUID):
        edges = []
        for outgoing_edge in bottom.read_outgoing_edges(src):
            for typedBy in bottom.read_outgoing_elements(outgoing_edge, "Morphism"):
                if typedBy == type_node:
                    edges.append(outgoing_edge)
                    break
        return edges

    def navigate_modelref(node: UUID):
        uuid = bottom.read_value(node)
        return UUID(uuid)

    def find_cardinality(class_node: UUID, type_node: UUID):
        upper_card_edges = find_outgoing_typed_by(class_node, type_node)
        if len(upper_card_edges) == 1:
            ref = bottom.read_edge_target(upper_card_edges[0])
            integer, = bottom.read_outgoing_elements(
                navigate_modelref(ref),
                "integer")
            # finally, the value we're looking for:
            return bottom.read_value(integer)

    def get_attributes(class_node: UUID):
        attr_edges = find_outgoing_typed_by(class_node, attr_link_node)
        result = []
        for attr_edge in attr_edges:
            name_edge, = find_outgoing_typed_by(attr_edge, attr_link_name_node)
            if name_edge == None:
                raise Exception("Expected attribute to have a name...")
            ref_name = bottom.read_edge_target(name_edge)
            string, = bottom.read_outgoing_elements(
                navigate_modelref(ref_name),
                "string")
            attr_name = bottom.read_value(string)
            ref_type = bottom.read_edge_target(attr_edge)
            typ = navigate_modelref(ref_type)
            result.append((attr_name, typ))
        return result

    ramified = state.create_node()
    ramified_scd = SCD(ramified, state)

    string_modelref = ramified_scd.create_model_ref("String", string_type)

    print()

    classes = scd.get_classes()
    for class_name, class_node in classes.items():
        # For every class in our original model, create a class:
        #   - abstract: False
        #   - min-card: 0
        #   - max-card: same as original
        upper_card = find_cardinality(class_node, class_upper_card_node)
        print('creating class', class_name, "with card 0 ..", upper_card)
        ramified_scd.create_class(class_name, abstract=None, max_c=upper_card)

        for (attr_name, attr_type) in get_attributes(class_node):
            print('  creating attribute', attr_name, "with type String")
            # Every attribute becomes 'string' type
            # The string will be a Python expression
            ramified_scd._create_attribute_link(class_name, string_modelref, attr_name, optional=False)

    associations = scd.get_associations()
    for assoc_name, assoc_node in associations.items():
        # For every association in our original model, create an association:
        #   - src-min-card: 0
        #   - src-max-card: same as original
        #   - tgt-min-card: 0
        #   - tgt-max-card: same as original
        src_upper_card = find_cardinality(assoc_node, src_upper_card_node)
        tgt_upper_card = find_cardinality(assoc_node, tgt_upper_card_node)
        src = scd.get_class_name(bottom.read_edge_source(assoc_node))
        tgt = scd.get_class_name(bottom.read_edge_target(assoc_node))
        print('creating assoc', src, "->", tgt, ", name =", assoc_name, ", src card = 0 ..", src_upper_card, "and tgt card = 0 ..", tgt_upper_card)
        ramified_scd.create_association(assoc_name, src, tgt,
            src_max_c=src_upper_card,
            tgt_max_c=tgt_upper_card)

    for inh_name, inh_node in scd.get_inheritances().items():
        # Re-create inheritance links like in our original model:
        src = scd.get_class_name(bottom.read_edge_source(inh_node))
        tgt = scd.get_class_name(bottom.read_edge_target(inh_node))
        print('creating inheritance link', src, '->', tgt)
        ramified_scd.create_inheritance(src, tgt)

    # The RAMified meta-model should also conform to 'SCD':
    conf = Conformance(state, ramified, scd_metamodel)
    print("conforms?", conf.check_nominal(log=True))

    return ramified