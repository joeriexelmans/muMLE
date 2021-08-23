from services.bottom.V0 import Bottom
from uuid import UUID
from state.base import State
from typing import Dict, Tuple, Set, Any, List
from pprint import pprint


class Conformance:
    def __init__(self, state: State, scd_model: UUID, model: UUID, type_model: UUID):
        self.state = state
        self.bottom = Bottom(state)
        self.scd_model = scd_model
        self.model = model
        self.type_model = type_model
        self.type_mapping: Dict[str, str] = {}
        self.model_names = {
            # map model elements to their names to prevent iterating too much
            self.bottom.read_outgoing_elements(self.model, e)[0]: e
            for e in self.bottom.read_keys(self.model)
        }
        self.type_model_names = {
            # map type model elements to their names to prevent iterating too much
            self.bottom.read_outgoing_elements(self.type_model, e)[0]: e
            for e in self.bottom.read_keys(self.type_model)
        }
        self.sub_types: Dict[str, Set[str]] = {
            k: set() for k in self.bottom.read_keys(self.type_model)
        }
        self.primitive_values: Dict[UUID, Any] = {}
        self.abstract_types: List[str] = []
        self.multiplicities: Dict[str, Tuple] = {}
        self.source_multiplicities: Dict[str, Tuple] = {}
        self.target_multiplicities: Dict[str, Tuple] = {}

    def check_nominal(self):
        steps = [
            self.check_typing,
            self.check_link_typing,
            self.check_multiplicities,
            self.check_constraints
        ]
        for step in steps:
            conforms = step()
            if not conforms:
                return False
        return True

    def read_attribute(self, m_element: UUID, attr_name: str):

        def has_label(_edge: UUID, _label):
            elems = self.bottom.read_outgoing_elements(_edge)
            for elem in elems:
                value = self.primitive_values.get(elem, self.bottom.read_value(elem))
                if value is not None and value == _label:
                    return True
            return False

        def get_outgoing_edge_by_label(_element: UUID, _label):
            edges = self.bottom.read_outgoing_edges(_element)
            for e in edges:
                if has_label(e, _label):
                    return e

        outgoing = self.bottom.read_outgoing_edges(m_element)
        for edge in outgoing:
            try:
                edge_name = self.model_names[edge]
                edge_type_name = self.type_mapping[edge_name]
                edge_type, = self.bottom.read_outgoing_elements(self.type_model, edge_type_name)
                edge_type_src = self.bottom.read_edge_source(edge_type)
                if get_outgoing_edge_by_label(edge_type_src, attr_name) == edge_type:
                    result = self.bottom.read_edge_target(edge)
                    return self.primitive_values.get(result, self.bottom.read_value(result))

            except KeyError:
                pass  # non-model edge, e.g. morphism link

    def precompute_sub_types(self):
        inh_element, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")
        inh_links = []
        for tm_element, tm_name in self.type_model_names.items():
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            if inh_element in morphisms:
                inh_links.append(tm_element)

        for link in inh_links:
            tm_source = self.bottom.read_edge_source(link)
            tm_target = self.bottom.read_edge_target(link)
            parent_name = self.type_model_names[tm_target]
            child_name = self.type_model_names[tm_source]
            self.sub_types[parent_name].add(child_name)

        stop = False
        while not stop:
            stop = True
            for child_name, child_children in self.sub_types.items():
                for parent_name, parent_children in self.sub_types.items():
                    if child_name in parent_children:
                        original_size = len(parent_children)
                        parent_children.update(child_children)
                        if len(parent_children) != original_size:
                            stop = False

    def deref_primitive_values(self):
        ref_element, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")
        string_element, = self.bottom.read_outgoing_elements(self.scd_model, "String")
        boolean_element, = self.bottom.read_outgoing_elements(self.scd_model, "Boolean")
        integer_element, = self.bottom.read_outgoing_elements(self.scd_model, "Integer")
        t_deref = []
        t_refs = []
        for tm_element, tm_name in self.type_model_names.items():
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            if ref_element in morphisms:
                t_refs.append(self.type_model_names[tm_element])
            elif string_element in morphisms:
                t_deref.append(tm_element)
            elif boolean_element in morphisms:
                t_deref.append(tm_element)
            elif integer_element in morphisms:
                t_deref.append(tm_element)

        for elem in t_deref:
            primitive_model = UUID(self.bottom.read_value(elem))
            primitive_value_node, = self.bottom.read_outgoing_elements(primitive_model)
            primitive_value = self.bottom.read_value(primitive_value_node)
            self.primitive_values[elem] = primitive_value

        for m_name, tm_name in self.type_mapping.items():
            if tm_name in t_refs:
                # dereference
                m_element, = self.bottom.read_outgoing_elements(self.model, m_name)
                primitive_model = UUID(self.bottom.read_value(m_element))
                try:
                    primitive_value_node, = self.bottom.read_outgoing_elements(primitive_model)
                    primitive_value = self.bottom.read_value(primitive_value_node)
                    self.primitive_values[m_element] = primitive_value
                except ValueError:
                    pass  # multiple elements in model indicate that we're not dealing with a primitive

    def precompute_multiplicities(self):
        for tm_element, tm_name in self.type_model_names.items():
            # class abstract flags and multiplicities
            abstract = self.read_attribute(tm_element, "abstract")
            lc = self.read_attribute(tm_element, "lower_cardinality")
            uc = self.read_attribute(tm_element, "upper_cardinality")
            if abstract:
                self.abstract_types.append(tm_name)
            if lc or uc:
                mult = (
                    lc if lc is not None else float("-inf"),
                    uc if uc is not None else float("inf")
                )
                self.multiplicities[tm_name] = mult
            # multiplicities for associations
            slc = self.read_attribute(tm_element, "source_lower_cardinality")
            suc = self.read_attribute(tm_element, "source_upper_cardinality")
            if slc or suc:
                mult = (
                    slc if slc is not None else float("-inf"),
                    suc if suc is not None else float("inf")
                )
                self.source_multiplicities[tm_name] = mult
            tlc = self.read_attribute(tm_element, "target_lower_cardinality")
            tuc = self.read_attribute(tm_element, "target_upper_cardinality")
            if tlc or tuc:
                mult = (
                    tlc if tlc is not None else float("-inf"),
                    tuc if tuc is not None else float("inf")
                )
                self.target_multiplicities[tm_name] = mult
            # optional for attribute links
            opt = self.read_attribute(tm_element, "optional")
            if opt is not None:
                mult = (0 if opt else 1, 1)
                self.source_multiplicities[tm_name] = mult
                self.target_multiplicities[tm_name] = mult

    def get_type(self, element: UUID):
        morphisms = self.bottom.read_outgoing_elements(element, "Morphism")
        tm_element, = [m for m in morphisms if m in self.type_model_names.keys()]
        return tm_element

    def check_typing(self):
        """
        for each element of model check whether a morphism
        link exists to some element of type_model
        """
        ref_element, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")
        model_names = self.bottom.read_keys(self.model)
        for m_name in model_names:
            m_element, = self.bottom.read_outgoing_elements(self.model, m_name)
            try:
                tm_element = self.get_type(m_element)
                tm_name = self.type_model_names[tm_element]
                self.type_mapping[m_name] = tm_name
                if ref_element in self.bottom.read_outgoing_elements(tm_element, "Morphism"):
                    sub_m = UUID(self.bottom.read_value(m_element))
                    sub_tm = UUID(self.bottom.read_value(tm_element))
                    if not Conformance(self.state, self.scd_model, sub_m, sub_tm).check_nominal():
                        return False
            except ValueError:
                # no or too many morphism links found
                print(f"Incorrectly typed element: {m_name}")
                return False
        return True

    def check_link_typing(self):
        self.precompute_sub_types()
        for m_name, tm_name in self.type_mapping.items():
            m_element, = self.bottom.read_outgoing_elements(self.model, m_name)
            m_source = self.bottom.read_edge_source(m_element)
            m_target = self.bottom.read_edge_target(m_element)
            if m_source is None or m_target is None:
                # element is not a link
                continue
            tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
            tm_source = self.bottom.read_edge_source(tm_element)
            tm_target = self.bottom.read_edge_target(tm_element)
            # check if source is typed correctly
            source_name = self.model_names[m_source]
            source_type_actual = self.type_mapping[source_name]
            source_type_expected = self.type_model_names[tm_source]
            if source_type_actual != source_type_expected:
                if source_type_actual not in self.sub_types[source_type_expected]:
                    print(f"Invalid source type {source_type_actual} for element {m_name}")
                    return False
            # check if target is typed correctly
            target_name = self.model_names[m_target]
            target_type_actual = self.type_mapping[target_name]
            target_type_expected = self.type_model_names[tm_target]
            if target_type_actual != target_type_expected:
                if target_type_actual not in self.sub_types[target_type_expected]:
                    print(f"Invalid target type {target_type_actual} for element {m_name}")
                    return False
        return True

    def check_multiplicities(self):
        self.deref_primitive_values()
        self.precompute_multiplicities()
        for tm_name in self.type_model_names.values():
            # abstract classes
            if tm_name in self.abstract_types:
                type_count = list(self.type_mapping.values()).count(tm_name)
                if type_count > 0:
                    print(f"Invalid instantiation of abstract class: {tm_name}")
                    return False
            # class multiplicities
            if tm_name in self.multiplicities:
                lc, uc = self.multiplicities[tm_name]
                type_count = list(self.type_mapping.values()).count(tm_name)
                for sub_type in self.sub_types[tm_name]:
                    type_count += list(self.type_mapping.values()).count(sub_type)
                if type_count < lc or type_count > uc:
                    print(f"Cardinality of type exceeds valid multiplicity range: {tm_name} ({type_count})")
                    return False
            # association source multiplicities
            if tm_name in self.source_multiplicities:
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                tm_source_element = self.bottom.read_edge_source(tm_element)
                tm_source_name = self.type_model_names[tm_source_element]
                lc, uc = self.source_multiplicities[tm_name]
                for i, t in self.type_mapping.items():
                    if t == tm_source_name or t in self.sub_types[tm_source_name]:
                        count = 0
                        i_element, = self.bottom.read_outgoing_elements(self.model, i)
                        outgoing = self.bottom.read_outgoing_edges(i_element)
                        for o in outgoing:
                            try:
                                if self.type_mapping[self.model_names[o]] == tm_name:
                                    count += 1
                            except KeyError:
                                pass  # for elements not part of model, e.g. morphism links
                        if count < lc or count > uc:
                            print(f"Source cardinality of type {tm_name} exceeds valid multiplicity range in {i}.")
                            return False

            # association target multiplicities
            if tm_name in self.target_multiplicities:
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                tm_target_element = self.bottom.read_edge_source(tm_element)
                tm_target_name = self.type_model_names[tm_target_element]
                lc, uc = self.target_multiplicities[tm_name]
                for i, t in self.type_mapping.items():
                    if t == tm_target_name or t in self.sub_types[tm_target_name]:
                        count = 0
                        i_element, = self.bottom.read_outgoing_elements(self.model, i)
                        outgoing = self.bottom.read_outgoing_edges(i_element)
                        for o in outgoing:
                            try:
                                if self.type_mapping[self.model_names[o]] == tm_name:
                                    count += 1
                            except KeyError:
                                pass  # for elements not part of model, e.g. morphism links
                        if count < lc or count > uc:
                            print(f"Target cardinality of type {tm_name} exceeds valid multiplicity range in {i}.")
                            return False
        return True

    def check_constraints(self):
        # local constraints
        for m_name, tm_name in self.type_mapping.items():
            if tm_name != "GlobalConstraint":
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                code = self.read_attribute(tm_element, "constraint")
                print(code)
        # global constraints
        for m_name, tm_name in self.type_mapping.items():
            if tm_name == "GlobalConstraint":
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                code = self.read_attribute(tm_element, "constraint")
                print(code)
        return True


def __create_pn(state: State):
    from services.scd import SCD
    # Retrieve refs to primitive type models
    # # integer
    int_type_id = state.read_dict(state.read_root(), "Integer")
    int_type = UUID(state.read_value(int_type_id))
    # # string
    str_type_id = state.read_dict(state.read_root(), "String")
    str_type = UUID(state.read_value(str_type_id))
    # Create LTM_PN
    model_uuid = state.create_node()
    service = SCD(scd, model_uuid, state)
    # Create classes
    service.create_class("P")
    service.create_class("T")
    # Create associations
    service.create_association("P2T", "P", "T")
    service.create_association("T2P", "T", "P")
    # Create model refs
    service.create_model_ref("Integer", int_type)
    service.create_model_ref("String", int_type)
    # Create class attributes
    service.create_attribute_link("P", "Integer", "t", False)
    service.create_attribute_link("P", "String", "n", False)
    service.create_attribute_link("T", "String", "n", False)
    # Create association attributes
    service.create_attribute_link("P2T", "Integer", "w", False)
    service.create_attribute_link("T2P", "Integer", "w", False)
    # Create test constraint
    service.add_constraint("P", "print(element)\nreturn True")
    return model_uuid


if __name__ == '__main__':
    from state.devstate import DevState as State
    s = State()
    from bootstrap.scd import bootstrap_scd
    scd = bootstrap_scd(s)
    pn = __create_pn(s)
    # cf = Conformance(s, scd, scd, scd)
    # cf.check_nominal()
    cf = Conformance(s, scd, pn, scd)
    cf.check_nominal()

