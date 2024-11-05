from services.bottom.V0 import Bottom
from services.primitives.actioncode_type import ActionCode
from uuid import UUID
from state.base import State
from typing import Dict, Tuple, Set, Any, List
from pprint import pprint
import traceback
from concrete_syntax.common import indent

from api.cd import CDAPI
from api.od import ODAPI

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
        return "CONFORM"
    else:
        joined = ''.join(('\n  ▸ ' + err for err in error_list))
        return f"NOT CONFORM, {len(error_list)} errors:{joined}"


class Conformance:
    # Parameter 'constraint_check_subtypes': whether to check local type-level constraints also on subtypes.
    def __init__(self, state: State, model: UUID, type_model: UUID, constraint_check_subtypes=True):
        self.state = state
        self.bottom = Bottom(state)
        self.model = model
        self.type_model = type_model
        self.constraint_check_subtypes = constraint_check_subtypes

        # MCL
        type_model_id = state.read_dict(state.read_root(), "SCD")
        self.scd_model = UUID(state.read_value(type_model_id))

        # Helpers
        self.cdapi = CDAPI(state, type_model)
        self.odapi = ODAPI(state, model, type_model)
        self.type_odapi = ODAPI(state, type_model, self.scd_model)

        # Pre-computed:
        self.abstract_types: List[str] = []
        self.multiplicities: Dict[str, Tuple] = {}
        self.source_multiplicities: Dict[str, Tuple] = {}
        self.target_multiplicities: Dict[str, Tuple] = {}

        # ?
        self.structures = {}
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

    def precompute_multiplicities(self):
        """
        Creates an internal representation of type multiplicities that is
        more easily queryable that the state graph
        """
        for clss_name, clss in self.type_odapi.get_all_instances("Class"):
            abstract = self.type_odapi.get_slot_value_default(clss, "abstract", default=False)
            if abstract:
                self.abstract_types.append(clss_name)

            lc = self.type_odapi.get_slot_value_default(clss, "lower_cardinality", default=0)
            uc = self.type_odapi.get_slot_value_default(clss, "upper_cardinality", default=float('inf'))
            if lc or uc:
                self.multiplicities[clss_name] = (lc, uc)

        for assoc_name, assoc in self.type_odapi.get_all_instances("Association"):
            # multiplicities for associations
            slc = self.type_odapi.get_slot_value_default(assoc, "source_lower_cardinality", default=0)
            suc = self.type_odapi.get_slot_value_default(assoc, "source_upper_cardinality", default=float('inf'))
            if slc or suc:
                self.source_multiplicities[assoc_name] = (slc, suc)
            tlc = self.type_odapi.get_slot_value_default(assoc, "target_lower_cardinality", default=0)
            tuc = self.type_odapi.get_slot_value_default(assoc, "target_upper_cardinality", default=float('inf'))
            if tlc or tuc:
                self.target_multiplicities[assoc_name] = (tlc, tuc)

        for attr_name, attr in self.type_odapi.get_all_instances("AttributeLink"):
            # optional for attribute links
            opt = self.type_odapi.get_slot_value(attr, "optional")
            if opt != None:
                self.source_multiplicities[attr_name] = (0, float('inf'))
                self.target_multiplicities[attr_name] = (0 if opt else 1, 1)

    def check_typing(self):
        """
        for each element of model check whether a morphism
        link exists to some element of type_model
        """
        errors = []

        # Recursively do a conformance check for each ModelRef
        for ref_name, ref in self.type_odapi.get_all_instances("ModelRef"):
            sub_mm = UUID(self.bottom.read_value(ref))
            for ref_inst_name, ref_inst in self.odapi.get_all_instances(ref_name):
                sub_m = UUID(self.bottom.read_value(ref_inst))
                nested_errors = Conformance(self.state, sub_m, sub_mm).check_nominal()
                errors += [f"In ModelRef ({m_name}):" + err for err in nested_errors]

        return errors

    def check_link_typing(self):
        """
        for each link, check whether its source and target are of a valid type
        """
        errors = []
        for tm_name, tm_element in self.type_odapi.get_all_instances("Association") + self.type_odapi.get_all_instances("AttributeLink"):
            for m_name, m_element in self.odapi.get_all_instances(tm_name):
                m_source = self.bottom.read_edge_source(m_element)
                m_target = self.bottom.read_edge_target(m_element)
                if m_source == None or m_target == None:
                    # element is not a link
                    continue
                # tm_element, = self.bottom.read_outgoing_elements(self.type_model, tm_name)
                tm_source = self.bottom.read_edge_source(tm_element)
                tm_target = self.bottom.read_edge_target(tm_element)
                # check if source is typed correctly
                # source_name = self.odapi.m_obj_to_name[m_source]
                source_type_actual = self.odapi.get_type_name(m_source)
                source_type_expected = self.odapi.mm_obj_to_name[tm_source]
                if not self.cdapi.is_subtype(super_type_name=source_type_expected, sub_type_name=source_type_actual):
                    errors.append(f"Invalid source type '{source_type_actual}' for link '{m_name}:{tm_name}'")
                # check if target is typed correctly
                # target_name = self.odapi.m_obj_to_name[m_target]
                target_type_actual = self.odapi.get_type_name(m_target)
                target_type_expected = self.odapi.mm_obj_to_name[tm_target]
                if not self.cdapi.is_subtype(super_type_name=source_type_expected, sub_type_name=source_type_actual):
                    errors.append(f"Invalid target type '{target_type_actual}' for link '{m_name}:{tm_name}'")
        return errors

    def check_multiplicities(self):
        """
        Check whether multiplicities for all types are respected
        """
        self.precompute_multiplicities()
        errors = []
        for class_name, clss in self.type_odapi.get_all_instances("Class"):
        # for type_name in self.odapi.mm_obj_to_name.values():
            # abstract classes
            if class_name in self.abstract_types:
                count = len(self.odapi.get_all_instances(class_name, include_subtypes=False))
                if count > 0:
                    errors.append(f"Invalid instantiation of abstract class: '{class_name}'")
            # class multiplicities
            if class_name in self.multiplicities:
                lc, uc = self.multiplicities[class_name]
                count = len(self.odapi.get_all_instances(class_name, include_subtypes=True))
                if count < lc or count > uc:
                    errors.append(f"Cardinality of type exceeds valid multiplicity range: '{class_name}' ({count})")

        for assoc_name, assoc in self.type_odapi.get_all_instances("Association") + self.type_odapi.get_all_instances("AttributeLink"):
            # association/attribute source multiplicities
            if assoc_name in self.source_multiplicities:
                # type is an association
                assoc, = self.bottom.read_outgoing_elements(self.type_model, assoc_name)
                tgt_type_obj = self.bottom.read_edge_target(assoc)
                tgt_type_name = self.odapi.mm_obj_to_name[tgt_type_obj]
                lc, uc = self.source_multiplicities[assoc_name]
                for obj_name, obj in self.odapi.get_all_instances(tgt_type_name, include_subtypes=True):
                    # obj's type has this incoming association -> now we will count the number of links typed by it
                    count = len(self.odapi.get_incoming(obj, assoc_name, include_subtypes=True))
                    if count < lc or count > uc:
                        errors.append(f"Source cardinality of type '{assoc_name}' ({count}) out of bounds ({lc}..{uc}) in '{obj_name}'.")

            # association/attribute target multiplicities
            if assoc_name in self.target_multiplicities:
                # type is an association
                type_obj, = self.bottom.read_outgoing_elements(self.type_model, assoc_name)
                src_type_obj = self.bottom.read_edge_source(type_obj)
                src_type_name = self.odapi.mm_obj_to_name[src_type_obj]
                lc, uc = self.target_multiplicities[assoc_name]
                for obj_name, obj in self.odapi.get_all_instances(src_type_name, include_subtypes=True):
                    # obj's type has this outgoing association -> now we will count the number of links typed by it
                    count = len(self.odapi.get_outgoing(obj, assoc_name, include_subtypes=True))
                    if count < lc or count > uc:
                        errors.append(f"Target cardinality of type '{assoc_name}' ({count}) out of bounds ({lc}..{uc}) in '{obj_name}'.")
        return errors

    def evaluate_constraint(self, code, **kwargs):
        """
        Evaluate constraint code (Python code)
        """

        funcs = {
            'read_value': self.state.read_value,
            'get': self.odapi.get,
            'get_value': self.odapi.get_value,
            'get_target': self.odapi.get_target,
            'get_source': self.odapi.get_source,
            'get_slot': self.odapi.get_slot,
            'get_slot_value': self.odapi.get_slot_value,
            'get_all_instances': self.odapi.get_all_instances,
            'get_name': self.odapi.get_name,
            'get_type_name': self.odapi.get_type_name,
            'get_outgoing': self.odapi.get_outgoing,
            'get_incoming': self.odapi.get_incoming,
            'has_slot': self.odapi.has_slot,
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
        return result

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
            if result == None:
                return # OK
            if isinstance(result, str):
                errors.append(f"{description} not satisfied. Reason: {result}")
            elif isinstance(result, bool):
                if not result:
                    errors.append(f"{description} not satisfied.")
            elif isinstance(result, list):
                if len(result) > 0:
                    reasons = indent('\n'.join(result), 4)
                    errors.append(f"{description} not satisfied. Reasons:\n{reasons}")
            else:
                raise Exception(f"{description} evaluation result should be boolean or string! Instead got {result}")

        # local constraints
        for type_name in self.bottom.read_keys(self.type_model):
            code = get_code(type_name)
            if code != None:
                instances = self.odapi.get_all_instances(type_name, include_subtypes=self.constraint_check_subtypes)
                for obj_name, obj_id in instances:
                    description = f"Local constraint of \"{type_name}\" in \"{obj_name}\""
                    # print(description)
                    try:
                        result = self.evaluate_constraint(code, this=obj_id) # may raise
                        check_result(result, description)
                    except:
                        errors.append(f"Runtime error during evaluation of {description}:\n{indent(traceback.format_exc(), 6)}")

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
                description = f"Global constraint \"{tm_name}\""
                try:
                    result = self.evaluate_constraint(code, model=self.model)
                except:
                    errors.append(f"Runtime error during evaluation of {description}:\n{indent(traceback.format_exc(), 6)}")
                check_result(result, description)
        return errors

    def precompute_structures(self):
        """
        Make an internal representation of type structures such that comparing type structures is easier
        """
        scd_elements = self.bottom.read_outgoing_elements(self.scd_model)
        # collect types
        class_element, = self.bottom.read_outgoing_elements(self.scd_model, "Class")
        association_element, = self.bottom.read_outgoing_elements(self.scd_model, "Association")
        for tm_element, tm_name in self.odapi.mm_obj_to_name.items():
            # retrieve elements that tm_element is a morphism of
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            morphism, = [m for m in morphisms if m in scd_elements]
            # check if tm_element is a morphism of AttributeLink
            if class_element == morphism or association_element == morphism:
                self.structures[tm_name] = set()
        # collect type structures
        # retrieve AttributeLink to check whether element is a morphism of AttributeLink
        attr_link_element, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink")
        for tm_element, tm_name in self.odapi.mm_obj_to_name.items():
            # retrieve elements that tm_element is a morphism of
            morphisms = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            morphism, = [m for m in morphisms if m in scd_elements]
            # check if tm_element is a morphism of AttributeLink
            if attr_link_element == morphism:
                # retrieve attributes of attribute link, i.e. 'name' and 'optional'
                attrs = self.bottom.read_outgoing_elements(tm_element)
                name_model_node, = filter(lambda x: self.odapi.m_obj_to_name.get(x, "").endswith(".name"), attrs)
                opt_model_node, = filter(lambda x: self.odapi.m_obj_to_name.get(x, "").endswith(".optional"), attrs)
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
                source_type_name = self.odapi.mm_obj_to_name[source_type_node]
                target_type_node = self.bottom.read_edge_target(tm_element)
                target_type_name = self.odapi.mm_obj_to_name[target_type_node]
                # add attribute to the structure of its source type
                # attribute is stored as a (name, optional, type) triple
                self.structures.setdefault(source_type_name, set()).add((name, opt, target_type_name))
        # extend structures of sub types with attrs of super types
        for super_type, sub_types in self.odapi.transitive_sub_types.items():
        # JE: I made an untested change here! Can't test because structural conformance checking is broken.
        # for super_type, sub_types in self.sub_types.items():
            for sub_type in sub_types:
                if sub_type != super_type:
                    self.structures.setdefault(sub_type, set()).update(self.structures[super_type])
        # filter out abstract types, as they cannot be instantiated
        # retrieve Class_abstract to check whether element is a morphism of Class_abstract
        class_abs_element, = self.bottom.read_outgoing_elements(self.scd_model, "Class_abstract")
        for tm_element, tm_name in self.odapi.mm_obj_to_name.items():
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
                type_name = self.odapi.mm_obj_to_name[source_node]
                if is_abstract:
                    self.structures.pop(type_name)

    def match_structures(self):
        """
        Try to match the structure of each element in the instance model to some element in the type model
        """
        ref_element, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")
        # matching
        for m_element, m_name in self.odapi.m_obj_to_name.items():
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
        for m_element, m_name in self.odapi.m_obj_to_name.items():
            is_edge = self.bottom.read_edge_source(m_element) != None
            if is_edge and m_name in self.candidates:
                m_source = self.bottom.read_edge_source(m_element)
                m_target = self.bottom.read_edge_target(m_element)
                print(self.candidates)
                source_candidates = self.candidates[self.odapi.m_obj_to_name[m_source]]
                target_candidates = self.candidates[self.odapi.m_obj_to_name[m_target]]
                remove = set()
                for candidate_name in self.candidates[m_name]:
                    candidate_element, = self.bottom.read_outgoing_elements(self.type_model, candidate_name)
                    candidate_source = self.odapi.mm_obj_to_name[self.bottom.read_edge_source(candidate_element)]
                    if candidate_source not in source_candidates:
                        if len(source_candidates.intersection(set(self.odapi.transitive_sub_types[candidate_source]))) == 0:
                        # if len(source_candidates.intersection(set(self.sub_types[candidate_source]))) == 0:
                            remove.add(candidate_name)
                    candidate_target = self.odapi.mm_obj_to_name[self.bottom.read_edge_target(candidate_element)]
                    if candidate_target not in target_candidates:
                        if len(target_candidates.intersection(set(self.odapi.transitive_sub_types[candidate_target]))) == 0:
                        # if len(target_candidates.intersection(set(self.sub_types[candidate_target]))) == 0:
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


