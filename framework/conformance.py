from services.bottom.V0 import Bottom
from services import od
from services.primitives.actioncode_type import ActionCode
from uuid import UUID
from state.base import State
from typing import Dict, Tuple, Set, Any, List
from pprint import pprint

import functools


# based on https://stackoverflow.com/a/39381428
# Parses and executes a block of Python code, and returns the eval result of the last statement
import ast
def exec_then_eval(code, _globals, _locals):
    block = ast.parse(code, mode='exec')
    # assumes last node is an expression
    last = ast.Expression(block.body.pop().value)
    exec(compile(block, '<string>', mode='exec'), _globals, _locals)
    return eval(compile(last, '<string>', mode='eval'), _globals, _locals)

def render_conformance_check_result(error_list):
    if len(error_list) == 0:
        return "OK"
    else:
        joined = '\n  '.join(error_list)
        return f"There were {len(error_list)} errors: \n  {joined}"


class Conformance:
    def __init__(self, state: State, model: UUID, type_model: UUID, constraint_check_subtypes=True):
        self.state = state
        self.bottom = Bottom(state)
        type_model_id = state.read_dict(state.read_root(), "SCD")
        self.scd_model = UUID(state.read_value(type_model_id))
        self.model = model
        self.type_model = type_model
        self.constraint_check_subtypes = constraint_check_subtypes # for a class-level constraint, also check the constraint on the subtypes of that class?
        self.type_mapping: Dict[str, str] = {}
        self.model_names = {
            # map model elements to their names to prevent iterating too much
            self.bottom.read_outgoing_elements(self.model, e)[0]: e
            for e in self.bottom.read_keys(self.model)
        }
        self.type_model_names = {
            # map type model elements to their names to prevent iterating too much
            self.bottom.read_outgoing_elements(self.type_model, e)[0]
                : e for e in self.bottom.read_keys(self.type_model)
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
        """
        Perform a nominal conformance check

        Args:
            log: boolean indicating whether to log errors

        Returns:
            Boolean indicating whether the check has passed
        """
        errors = []
        errors += self.check_typing()
        errors += self.check_link_typing()
        errors += self.check_multiplicities()
        errors += self.check_constraints()
        return errors

    # def check_structural(self, *, build_morphisms=True, log=False):
    #     """
    #     Perform a structural conformance check

    #     Args:
    #         build_morphisms: boolean indicating whether to create morpishm links
    #         log: boolean indicating whether to log errors

    #     Returns:
    #         Boolean indicating whether the check has passed
    #     """
    #     try:
    #         self.precompute_structures()
    #         self.match_structures()
    #         if build_morphisms:
    #             self.build_morphisms()
    #             self.check_nominal(log=log)
    #         return True
    #     except RuntimeError as e:
    #         if log:
    #             print(e)
    #         return False

    def read_attribute(self, element: UUID, attr_name: str):
        """
        Read an attribute value attached to an element

        Args:
            element: UUID of the element
            attr_name: name of the attribute to read

        Returns:
            The value of hte attribute, if no attribute with given name is found, returns None
        """
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
            return self.primitive_values.get(attr_elem, self.bottom.read_value(UUID(self.bottom.read_value(attr_elem))))
        except ValueError:
            return None

    def precompute_sub_types(self):
        """
        Creates an internal representation of sub-type hierarchies that is
        more easily queryable that the state graph
        """
        # collect inheritance link instances
        inh_element, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")
        inh_links = []
        for tm_element, tm_name in self.type_model_names.items():
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            if inh_element in morphisms:
                # we have an instance of an inheritance link
                inh_links.append(tm_element)

        # for each inheritance link we add the parent and child to the sub types map
        for link in inh_links:
            tm_source = self.bottom.read_edge_source(link)
            tm_target = self.bottom.read_edge_target(link)
            parent_name = self.type_model_names[tm_target]
            child_name = self.type_model_names[tm_source]
            self.sub_types[parent_name].add(child_name)

        # iteratively expand the sub type hierarchies in the sub types map
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
        """
        Prefetch the values stored in referenced primitive type models
        """
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
        """
        Creates an internal representation of type multiplicities that is
        more easily queryable that the state graph
        """
        for tm_element, tm_name in self.type_model_names.items():
            # class abstract flags and multiplicities
            abstract = self.read_attribute(tm_element, "abstract")
            lc = self.read_attribute(tm_element, "lower_cardinality")
            uc = self.read_attribute(tm_element, "upper_cardinality")
            if abstract:
                self.abstract_types.append(tm_name)
            if lc or uc:
                mult = (
                    lc if lc != None else float("-inf"),
                    uc if uc != None else float("inf")
                )
                self.multiplicities[tm_name] = mult
            # multiplicities for associations
            slc = self.read_attribute(tm_element, "source_lower_cardinality")
            suc = self.read_attribute(tm_element, "source_upper_cardinality")
            if slc or suc:
                mult = (
                    slc if slc != None else float("-inf"),
                    suc if suc != None else float("inf")
                )
                self.source_multiplicities[tm_name] = mult
            tlc = self.read_attribute(tm_element, "target_lower_cardinality")
            tuc = self.read_attribute(tm_element, "target_upper_cardinality")
            if tlc or tuc:
                mult = (
                    tlc if tlc != None else float("-inf"),
                    tuc if tuc != None else float("inf")
                )
                self.target_multiplicities[tm_name] = mult
            # optional for attribute links
            opt = self.read_attribute(tm_element, "optional")
            if opt != None:
                self.source_multiplicities[tm_name] = (0, float('inf'))
                self.target_multiplicities[tm_name] = (0 if opt else 1, 1)

    def get_type(self, element: UUID):
        """
        Retrieve the type of an element (wrt. current type model)
        """
        morphisms = self.bottom.read_outgoing_elements(element, "Morphism")
        tm_element, = [m for m in morphisms if m in self.type_model_names.keys()]
        return tm_element

    def check_typing(self):
        """
        for each element of model check whether a morphism
        link exists to some element of type_model
        """
        errors = []
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
                    nested_errors = Conformance(self.state, sub_m, sub_tm).check_nominal()
                    errors += [f"In ModelRef ({m_name}):" + err for err in nested_errors]
            except ValueError as e:
                import traceback
                traceback.format_exc(e)
                # no or too many morphism links found
                errors.append(f"Incorrectly typed element: {m_name}")
        return errors

    def check_link_typing(self):
        """
        for each link, check whether its source and target are of a valid type
        """
        errors = []
        self.precompute_sub_types()
        for m_name, tm_name in self.type_mapping.items():
            m_element, = self.bottom.read_outgoing_elements(self.model, m_name)
            m_source = self.bottom.read_edge_source(m_element)
            m_target = self.bottom.read_edge_target(m_element)
            if m_source == None or m_target == None:
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
                    errors.append(f"Invalid source type {source_type_actual} for element {m_name}")
            # check if target is typed correctly
            target_name = self.model_names[m_target]
            target_type_actual = self.type_mapping[target_name]
            target_type_expected = self.type_model_names[tm_target]
            if target_type_actual != target_type_expected:
                if target_type_actual not in self.sub_types[target_type_expected]:
                    errors.append(f"Invalid target type {target_type_actual} for element {m_name}")
        return errors

    def check_multiplicities(self):
        """
        Check whether multiplicities for all types are respected
        """
        self.deref_primitive_values()
        self.precompute_multiplicities()
        errors = []
        for tm_name in self.type_model_names.values():
            # abstract classes
            if tm_name in self.abstract_types:
                type_count = list(self.type_mapping.values()).count(tm_name)
                if type_count > 0:
                    errors.append(f"Invalid instantiation of abstract class: {tm_name}")
            # class multiplicities
            if tm_name in self.multiplicities:
                lc, uc = self.multiplicities[tm_name]
                type_count = list(self.type_mapping.values()).count(tm_name)
                for sub_type in self.sub_types[tm_name]:
                    type_count += list(self.type_mapping.values()).count(sub_type)
                if type_count < lc or type_count > uc:
                    errors.append(f"Cardinality of type exceeds valid multiplicity range: {tm_name} ({type_count})")
            # association source multiplicities
            if tm_name in self.source_multiplicities:
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                tm_tgt_element = self.bottom.read_edge_target(tm_element)
                tm_tgt_name = self.type_model_names[tm_tgt_element]
                lc, uc = self.source_multiplicities[tm_name]
                for tgt_obj_name, t in self.type_mapping.items():
                    if t == tm_tgt_name or t in self.sub_types[tm_tgt_name]:
                        count = 0
                        tgt_obj_node, = self.bottom.read_outgoing_elements(self.model, tgt_obj_name)
                        incoming = self.bottom.read_incoming_edges(tgt_obj_node)
                        for i in incoming:
                            try:
                                if self.type_mapping[self.model_names[i]] == tm_name:
                                    count += 1
                            except KeyError:
                                pass  # for elements not part of model, e.g. morphism links
                        if count < lc or count > uc:
                            errors.append(f"Source cardinality of type {tm_name} ({count}) out of bounds ({lc}..{uc}) in {tgt_obj_name}.")

            # association target multiplicities
            if tm_name in self.target_multiplicities:
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                # tm_target_element = self.bottom.read_edge_target(tm_element)
                tm_src_element = self.bottom.read_edge_source(tm_element)
                tm_src_name = self.type_model_names[tm_src_element]
                lc, uc = self.target_multiplicities[tm_name]
                # print("checking assoc", tm_name, "source", tm_src_name)
                # print("subtypes of", tm_src_name, self.sub_types[tm_src_name])
                for src_obj_name, t in self.type_mapping.items():
                    if t == tm_src_name or t in self.sub_types[tm_src_name]:
                        # print("got obj", src_obj_name, "of type", t)
                        count = 0
                        src_obj_node, = self.bottom.read_outgoing_elements(self.model, src_obj_name)
                        # outgoing = self.bottom.read_incoming_edges(src_obj_node)
                        outgoing = self.bottom.read_outgoing_edges(src_obj_node)
                        for o in outgoing:
                            try:
                                if self.type_mapping[self.model_names[o]] == tm_name:
                                    # print("have an outgoing edge", self.model_names[o], self.type_mapping[self.model_names[o]], "---> increase counter")
                                    count += 1
                            except KeyError:
                                pass  # for elements not part of model, e.g. morphism links
                        if count < lc or count > uc:
                            errors.append(f"Target cardinality of type {tm_name} ({count}) out of bounds ({lc}..{uc}) in {src_obj_name}.")
                        # else:
                            # print(f"OK: Target cardinality of type {tm_name} ({count}) within bounds ({lc}..{uc}) in {src_obj_name}.")
        return errors

    def evaluate_constraint(self, code, **kwargs):
        """
        Evaluate constraint code (Python code)
        """

        funcs = {
            'read_value': self.state.read_value,
            'get_value': lambda el: od.read_primitive_value(self.bottom, el, self.type_model)[0],
            'get_target': lambda el: self.bottom.read_edge_target(el),
            'get_source': lambda el: self.bottom.read_edge_source(el),
            'get_slot': od.OD(self.type_model, self.model, self.state).get_slot,
            'get_all_instances': self.get_all_instances,
            'get_name': self.get_name,
            'get_type_name': self.get_type_name,
            'get_outgoing': self.get_outgoing,
            'get_incoming': self.get_incoming,
        }
        # print("evaluating constraint ...", code)
        loc = {**kwargs, }
        result = exec_then_eval(
            code,
            {'__builtins__': {'isinstance': isinstance, 'print': print,
                              'int': int, 'float': float, 'bool': bool, 'str': str, 'tuple': tuple, 'len': len, 'set': set, 'dict': dict},
                **funcs
             },  # globals
             loc # locals
        )
        # print('result =', result)
        return result

    def get_name(self, element: UUID):
        return [name for name in self.bottom.read_keys(self.model) if self.bottom.read_outgoing_elements(self.model, name)[0] == element][0]

    def get_type_name(self, element: UUID):
        type_node = self.bottom.read_outgoing_elements(element, "Morphism")[0]
        for type_name in self.bottom.read_keys(self.type_model):
            if self.bottom.read_outgoing_elements(self.type_model, type_name)[0] == type_node:
                return type_name

    def get_all_instances(self, type_name: str, include_subtypes=True):
        result = [e_name for e_name, t_name in self.type_mapping.items() if t_name == type_name]
        if include_subtypes:
            for subtype_name in self.sub_types[type_name]:
                # print(subtype_name, 'is subtype of ')
                result += [e_name for e_name, t_name in self.type_mapping.items() if t_name == subtype_name]
        result_with_ids = [ (e_name, self.bottom.read_outgoing_elements(self.model, e_name)[0]) for e_name in result]
        return result_with_ids

    def get_outgoing(self, element: UUID, assoc_or_attr_name: str):
        return od.find_outgoing_typed_by(self.bottom, src=element, type_node=self.bottom.read_outgoing_elements(self.type_model, assoc_or_attr_name)[0])

    def get_incoming(self, element: UUID, assoc_or_attr_name: str):
        return od.find_incoming_typed_by(self.bottom, tgt=element, type_node=self.bottom.read_outgoing_elements(self.type_model, assoc_or_attr_name)[0])

    def check_constraints(self):
        """
        Check whether all constraints defined for a model are respected
        """
        errors = []

        def get_code(tm_name):
            constraints = self.bottom.read_outgoing_elements(self.type_model, f"{tm_name}.constraint")
            if len(constraints) == 1:
                constraint = constraints[0]
                code = ActionCode(UUID(self.bottom.read_value(constraint)), self.bottom.state).read()
                return code

        def check_result(result, description):
            if not isinstance(result, bool):
                raise Exception(f"{description} evaluation result is not boolean! Instead got {result}")
            if not result:
                errors.append(f"{description} not satisfied.")

        # local constraints
        for type_name in self.bottom.read_keys(self.type_model):
            code = get_code(type_name)
            if code != None:
                instances = self.get_all_instances(type_name, include_subtypes=self.constraint_check_subtypes)
                for obj_name, obj_id in instances:
                    result = self.evaluate_constraint(code, this=obj_id)
                    description = f"Local constraint of \"{type_name}\" in \"{obj_name}\""
                    check_result(result, description)

        # global constraints
        glob_constraints = []
        # find global constraints...
        glob_constraint_type, = self.bottom.read_outgoing_elements(self.scd_model, "GlobalConstraint")
        for tm_name in self.bottom.read_keys(self.type_model):
            tm_node, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
            # print(key,  node)
            for type_of_node in self.bottom.read_outgoing_elements(tm_node, "Morphism"):
                if type_of_node == glob_constraint_type:
                    # node is GlobalConstraint
                    glob_constraints.append(tm_name)
        # evaluate them (each constraint once)
        for tm_name in glob_constraints:
            code = get_code(tm_name)
            if code != None:
                result = self.evaluate_constraint(code, model=self.model)
                description = f"Global constraint \"{tm_name}\""
                check_result(result, description)
        return errors

    def precompute_structures(self):
        """
        Make an internal representation of type structures such that comparing type structures is easier
        """
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
        """
        Try to match the structure of each element in the instance model to some element in the type model
        """
        ref_element, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")
        # matching
        for m_element, m_name in self.model_names.items():
            is_edge = self.bottom.read_edge_source(m_element) != None
            print('element:', m_element, 'name:', m_name, 'is_edge', is_edge)
            for type_name, structure in self.structures.items():
                tm_element, = self.bottom.read_outgoing_elements(self.type_model, type_name)
                type_is_edge = self.bottom.read_edge_source(tm_element) != None
                if is_edge == type_is_edge:
                    print('  type_name:', type_name, 'type_is_edge:', type_is_edge, "structure:", structure)
                    mismatch = False
                    matched = 0
                    for name, optional, attr_type in structure:
                        print('    name:', name, "optional:", optional, "attr_type:", attr_type)
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
                                if code != None:
                                    attr_conforms = self.evaluate_constraint(code, this=attr)
                            if attr_conforms:
                                matched += 1
                                print("     attr_conforms -> matched:", matched)
                        except ValueError as e:
                            # attr not found or failed parsing UUID
                            if optional:
                                print("     skipping:", e)
                                continue
                            else:
                                # did not match mandatory attribute
                                print("     breaking:", e)
                                mismatch = True
                                break

                    print('  matched:', matched, 'len(structure):', len(structure))
                    # if matched == len(structure):
                    if not mismatch:
                        print('  add to candidates:', m_name, type_name)
                        self.candidates.setdefault(m_name, set()).add(type_name)
        # filter out candidates for links based on source and target types
        for m_element, m_name in self.model_names.items():
            is_edge = self.bottom.read_edge_source(m_element) != None
            if is_edge and m_name in self.candidates:
                m_source = self.bottom.read_edge_source(m_element)
                m_target = self.bottom.read_edge_target(m_element)
                print(self.candidates)
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
        """
        Build the morphisms between an instance and a type model that structurally match
        """
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
                    attr_link_element, = self.bottom.read_outgoing_elements(self.model, f"{m_name}_{attr_name}")
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


