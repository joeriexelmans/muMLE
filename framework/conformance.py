from services.bottom.V0 import Bottom
from uuid import UUID
from state.base import State
from typing import Dict, Tuple, Set, Any, List
from pprint import pprint


class Conformance:
    def __init__(self, state: State, model: UUID, type_model: UUID):
        self.state = state
        self.bottom = Bottom(state)
        type_model_id = state.read_dict(state.read_root(), "SCD")
        self.scd_model = UUID(state.read_value(type_model_id))
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
        self.structures = {}
        self.matches = {}
        self.candidates = {}

    def check_nominal(self, *, log=False):
        try:
            self.check_typing()
            self.check_link_typing()
            self.check_multiplicities()
            self.check_constraints()
            return True
        except RuntimeError as e:
            if log:
                print(e)
            return False

    def check_structural(self, *, build_morphisms=True, log=False):
        try:
            self.precompute_structures()
            self.match_structures()
            if build_morphisms:
                self.build_morphisms()
                self.check_nominal(log=log)
            return True
        except RuntimeError as e:
            if log:
                print(e)
            return False

    def read_attribute(self, element: UUID, attr_name: str):

        if element in self.type_model_names:
            # type model element
            element_name = self.type_model_names[element]
            model = self.type_model
        else:
            # model element
            element_name = self.model_names[element]
            model = self.model
        try:
            attr_elem, = self.bottom.read_outgoing_elements(model, f"{element_name}.{attr_name}")
            return self.primitive_values.get(attr_elem, self.bottom.read_value(attr_elem))
        except ValueError:
            return None

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
                self.source_multiplicities[tm_name] = (0 if opt else 1, 1)
                self.target_multiplicities[tm_name] = (0, 1)

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
                    if not Conformance(self.state, sub_m, sub_tm).check_nominal():
                        raise RuntimeError(f"Incorrectly model reference: {m_name}")
            except ValueError:
                # no or too many morphism links found
                raise RuntimeError(f"Incorrectly typed element: {m_name}")
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
                    raise RuntimeError(f"Invalid source type {source_type_actual} for element {m_name}")
            # check if target is typed correctly
            target_name = self.model_names[m_target]
            target_type_actual = self.type_mapping[target_name]
            target_type_expected = self.type_model_names[tm_target]
            if target_type_actual != target_type_expected:
                if target_type_actual not in self.sub_types[target_type_expected]:
                    raise RuntimeError(f"Invalid target type {target_type_actual} for element {m_name}")
        return True

    def check_multiplicities(self):
        self.deref_primitive_values()
        self.precompute_multiplicities()
        for tm_name in self.type_model_names.values():
            # abstract classes
            if tm_name in self.abstract_types:
                type_count = list(self.type_mapping.values()).count(tm_name)
                if type_count > 0:
                    raise RuntimeError(f"Invalid instantiation of abstract class: {tm_name}")
            # class multiplicities
            if tm_name in self.multiplicities:
                lc, uc = self.multiplicities[tm_name]
                type_count = list(self.type_mapping.values()).count(tm_name)
                for sub_type in self.sub_types[tm_name]:
                    type_count += list(self.type_mapping.values()).count(sub_type)
                if type_count < lc or type_count > uc:
                    raise RuntimeError(f"Cardinality of type exceeds valid multiplicity range: {tm_name} ({type_count})")
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
                            raise RuntimeError(f"Source cardinality of type {tm_name} exceeds valid multiplicity range in {i}.")

            # association target multiplicities
            if tm_name in self.target_multiplicities:
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                tm_target_element = self.bottom.read_edge_target(tm_element)
                tm_target_name = self.type_model_names[tm_target_element]
                lc, uc = self.target_multiplicities[tm_name]
                for i, t in self.type_mapping.items():
                    if t == tm_target_name or t in self.sub_types[tm_target_name]:
                        count = 0
                        i_element, = self.bottom.read_outgoing_elements(self.model, i)
                        outgoing = self.bottom.read_incoming_edges(i_element)
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

    def evaluate_constraint(self, code, **kwargs):
        funcs = {
            'read_value': self.state.read_value
        }
        return eval(
            code,
            {'__builtins__': {'isinstance': isinstance, 'print': print,
                              'int': int, 'float': float, 'bool': bool, 'str': str, 'tuple': tuple}
             },  # globals
            {**kwargs, **funcs}  # locals
        )

    def check_constraints(self):
        # local constraints
        for m_name, tm_name in self.type_mapping.items():
            if tm_name != "GlobalConstraint":
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                code = self.read_attribute(tm_element, "constraint")
                if code is not None:
                    morphisms = self.bottom.read_incoming_elements(tm_element, "Morphism")
                    morphisms = [m for m in morphisms if m in self.model_names]
                    for m_element in morphisms:
                        if not self.evaluate_constraint(code, element=m_element):
                            raise RuntimeError(f"Local constraint of {tm_name} not satisfied in {m_name}.")

        # global constraints
        for m_name, tm_name in self.type_mapping.items():
            if tm_name == "GlobalConstraint":
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                code = self.read_attribute(tm_element, "constraint")
                if code is not None:
                    if not self.evaluate_constraint(code, model=self.model):
                        raise RuntimeError(f"Global constraint {tm_name} not satisfied.")
        return True

    def precompute_structures(self):
        self.precompute_sub_types()
        scd_elements = self.bottom.read_outgoing_elements(self.scd_model)
        # collect types
        class_element, = self.bottom.read_outgoing_elements(self.scd_model, "Class")
        association_element, = self.bottom.read_outgoing_elements(self.scd_model, "Association")
        for tm_element, tm_name in self.type_model_names.items():
            # retrieve elements that tm_element is a morphism of
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            morphism, = [m for m in morphisms if m in scd_elements]
            # check if tm_element is a morphism of AttributeLink
            if class_element == morphism or association_element == morphism:
                self.structures[tm_name] = set()
        # collect type structures
        # retrieve AttributeLink to check whether element is a morphism of AttributeLink
        attr_link_element, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink")
        for tm_element, tm_name in self.type_model_names.items():
            # retrieve elements that tm_element is a morphism of
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            morphism, = [m for m in morphisms if m in scd_elements]
            # check if tm_element is a morphism of AttributeLink
            if attr_link_element == morphism:
                # retrieve attributes of attribute link, i.e. 'name' and 'optional'
                attrs = self.bottom.read_outgoing_elements(tm_element)
                name_model_node, = filter(lambda x: self.type_model_names.get(x, "").endswith(".name"), attrs)
                opt_model_node, = filter(lambda x: self.type_model_names.get(x, "").endswith(".optional"), attrs)
                # get attr name value
                name_model = UUID(self.bottom.read_value(name_model_node))
                name_node, = self.bottom.read_outgoing_elements(name_model)
                name = self.bottom.read_value(name_node)
                # get attr opt value
                opt_model = UUID(self.bottom.read_value(opt_model_node))
                opt_node, = self.bottom.read_outgoing_elements(opt_model)
                opt = self.bottom.read_value(opt_node)
                # get attr type name
                source_type_node = self.bottom.read_edge_source(tm_element)
                source_type_name = self.type_model_names[source_type_node]
                target_type_node = self.bottom.read_edge_target(tm_element)
                target_type_name = self.type_model_names[target_type_node]
                # add attribute to the structure of its source type
                # attribute is stored as a (name, optional, type) triple
                self.structures.setdefault(source_type_name, set()).add((name, opt, target_type_name))
        # extend structures of sub types with attrs of super types
        for super_type, sub_types in self.sub_types.items():
            for sub_type in sub_types:
                self.structures.setdefault(sub_type, set()).update(self.structures[super_type])
        # filter out abstract types, as they cannot be instantiated
        # retrieve Class_abstract to check whether element is a morphism of Class_abstract
        class_abs_element, = self.bottom.read_outgoing_elements(self.scd_model, "Class_abstract")
        for tm_element, tm_name in self.type_model_names.items():
            # retrieve elements that tm_element is a morphism of
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            morphism, = [m for m in morphisms if m in scd_elements]
            # check if tm_element is a morphism of Class_abstract
            if class_abs_element == morphism:
                # retrieve 'abstract' attribute value
                target_node = self.bottom.read_edge_target(tm_element)
                abst_model = UUID(self.bottom.read_value(target_node))
                abst_node, = self.bottom.read_outgoing_elements(abst_model)
                is_abstract = self.bottom.read_value(abst_node)
                # retrieve type name
                source_node = self.bottom.read_edge_source(tm_element)
                type_name = self.type_model_names[source_node]
                if is_abstract:
                    self.structures.pop(type_name)

    def match_structures(self):
        ref_element, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")
        # matching
        for m_element, m_name in self.model_names.items():
            is_edge = self.bottom.read_edge_source(m_element) is not None
            for type_name, structure in self.structures.items():
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, type_name)
                type_is_edge = self.bottom.read_edge_source(tm_element) is not None
                if is_edge == type_is_edge:
                    matched = 0
                    for name, optional, attr_type in structure:
                        try:
                            attr, = self.bottom.read_outgoing_elements(self.model, f"{m_name}.{name}")
                            attr_tm, = self.bottom.read_outgoing_elements(self.type_model, attr_type)
                            # if attribute is a modelref, we need to check whether it
                            # linguistically conforms to the specified type
                            # if its an internally defined attribute, this will be checked by constraints
                            morphisms = self.bottom.read_outgoing_elements(attr_tm, "Morphism")
                            attr_conforms = True
                            if ref_element in morphisms:
                                # check conformance of reference model
                                type_model_uuid = UUID(self.bottom.read_value(attr_tm))
                                model_uuid = UUID(self.bottom.read_value(attr))
                                attr_conforms = Conformance(self.state, model_uuid, type_model_uuid)\
                                    .check_nominal()
                            else:
                                # eval constraints
                                code = self.read_attribute(attr_tm, "constraint")
                                if code is not None:
                                    attr_conforms = self.evaluate_constraint(code, element=attr)
                            if attr_conforms:
                                matched += 1
                        except ValueError:
                            # attr not found or failed parsing UUID
                            if optional:
                                continue
                            else:
                                break
                    if matched == len(structure):
                        self.candidates.setdefault(m_name, set()).add(type_name)
        # filter out candidates for links based on source and target types
        for m_element, m_name in self.model_names.items():
            is_edge = self.bottom.read_edge_source(m_element) is not None
            if is_edge and m_name in self.candidates:
                m_source = self.bottom.read_edge_source(m_element)
                m_target = self.bottom.read_edge_target(m_element)
                source_candidates = self.candidates[self.model_names[m_source]]
                target_candidates = self.candidates[self.model_names[m_target]]
                remove = set()
                for candidate_name in self.candidates[m_name]:
                    candidate_element, = self.bottom.read_outgoing_elements(self.type_model, candidate_name)
                    candidate_source = self.type_model_names[self.bottom.read_edge_source(candidate_element)]
                    if candidate_source not in source_candidates:
                        if len(source_candidates.intersection(set(self.sub_types[candidate_source]))) == 0:
                            remove.add(candidate_name)
                    candidate_target = self.type_model_names[self.bottom.read_edge_target(candidate_element)]
                    if candidate_target not in target_candidates:
                        if len(target_candidates.intersection(set(self.sub_types[candidate_target]))) == 0:
                            remove.add(candidate_name)
                self.candidates[m_name] = self.candidates[m_name].difference(remove)

    def build_morphisms(self):
        if not all([len(c) == 1 for c in self.candidates.values()]):
            raise RuntimeError("Cannot build incomplete or ambiguous morphism.")
        mapping = {k: v.pop() for k, v in self.candidates.items()}
        for m_name, tm_name in mapping.items():
            # morphism to class/assoc
            m_element, = self.bottom.read_outgoing_elements(self.model, m_name)
            tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
            self.bottom.create_edge(m_element, tm_element, "Morphism")
            # morphism for attributes and attribute links
            structure = self.structures[tm_name]
            for attr_name, _, attr_type in structure:
                try:
                    # attribute node
                    attr_element, = self.bottom.read_outgoing_elements(self.model, f"{m_name}.{attr_name}")
                    attr_type_element, = self.bottom.read_outgoing_elements(self.type_model, attr_type)
                    self.bottom.create_edge(attr_element, attr_type_element, "Morphism")
                    # attribute link
                    attr_link_element, = self.bottom.read_outgoing_elements(self.model, f"{m_name}.{attr_name}_link")
                    attr_link_type_element, = self.bottom.read_outgoing_elements(self.type_model, f"{tm_name}_{attr_name}")
                    self.bottom.create_edge(attr_link_element, attr_link_type_element, "Morphism")
                except ValueError:
                    pass


if __name__ == '__main__':
    from state.devstate import DevState as State
    s = State()
    from bootstrap.scd import bootstrap_scd
    scd = bootstrap_scd(s)
    from bootstrap.pn import bootstrap_pn
    ltm_pn = bootstrap_pn(s, "PN")
    ltm_pn_lola = bootstrap_pn(s, "PNlola")
    from services.pn import PN
    my_pn = s.create_node()
    PNserv = PN(my_pn, s)
    PNserv.create_place("p1", 5)
    PNserv.create_place("p2", 0)
    PNserv.create_transition("t1")
    PNserv.create_p2t("p1", "t1", 1)
    PNserv.create_t2p("t1", "p2", 1)
    
    cf = Conformance(s, my_pn, ltm_pn_lola)
    # cf = Conformance(s, scd, ltm_pn, scd)
    cf.precompute_structures()
    cf.match_structures()
    cf.build_morphisms()
    print(cf.check_nominal())


