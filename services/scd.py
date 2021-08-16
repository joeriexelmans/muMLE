from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.boolean_type import Boolean
from services.primitives.integer_type import Integer
from services.primitives.string_type import String

import re


class SCD:
    def __init__(self, scd_model: UUID, model: UUID, state: State):
        self.scd_model = scd_model
        self.model = model
        self.bottom = Bottom(state)

    def create_class(self, name: str, abstract: bool = None, min_c: int = None, max_c: int = None):
        
        def set_cardinality(bound: str, value: int):
            _c_model = self.bottom.create_node()
            Integer(_c_model, self.bottom.state).create(value)
            _c_node = self.bottom.create_node(str(_c_model))
            self.bottom.create_edge(self.model, _c_node, f"{name}.{bound}_cardinality")
            _c_link = self.bottom.create_edge(class_node, _c_node)
            self.bottom.create_edge(self.model, _c_link, f"{name}.{bound}_cardinality_link")
            _scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Integer")
            _scd_link, = self.bottom.read_outgoing_elements(self.scd_model, f"Class_{bound}_cardinality")
            self.bottom.create_edge(_c_node, _scd_node, "Morphism")
            self.bottom.create_edge(_c_link, _scd_link, "Morphism")
        
        # create class + attributes + morphism links
        class_node = self.bottom.create_node()  # create class node
        self.bottom.create_edge(self.model, class_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Class")  # retrieve type
        self.bottom.create_edge(class_node, scd_node, "Morphism")  # create morphism link
        if abstract is not None:
            abstract_model = self.bottom.create_node()
            Boolean(abstract_model, self.bottom.state).create(abstract)
            abstract_node = self.bottom.create_node(str(abstract_model))
            self.bottom.create_edge(self.model, abstract_node, f"{name}.abstract")
            abstract_link = self.bottom.create_edge(class_node, abstract_node)
            self.bottom.create_edge(self.model, abstract_link, f"{name}.abstract_link")
            scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Boolean")
            scd_link, = self.bottom.read_outgoing_elements(self.scd_model, "Class_abstract")
            self.bottom.create_edge(abstract_node, scd_node, "Morphism")
            self.bottom.create_edge(abstract_link, scd_link, "Morphism")
        if min_c is not None:
            set_cardinality("lower", min_c)
        if max_c is not None:
            set_cardinality("upper", min_c)

    def create_association(self, name: str, source: str, target: str,
                           src_min_c: int = None, src_max_c: int = None,
                           tgt_min_c: int = None, tgt_max_c: int = None):

        def set_cardinality(bound: str, value: int):
            _c_model = self.bottom.create_node()
            Integer(_c_model, self.bottom.state).create(value)
            _c_node = self.bottom.create_node(str(_c_model))
            self.bottom.create_edge(self.model, _c_node, f"{name}.{bound}_cardinality")
            _c_link = self.bottom.create_edge(assoc_edge, _c_node)
            self.bottom.create_edge(self.model, _c_link, f"{name}.{bound}_cardinality_link")
            _scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Integer")
            _scd_link, = self.bottom.read_outgoing_elements(self.scd_model, f"Class_{bound}_cardinality")
            self.bottom.create_edge(_c_node, _scd_node, "Morphism")
            self.bottom.create_edge(_c_link, _scd_link, "Morphism")

        # create class + attributes + morphism links
        assoc_edge = self.bottom.create_edge(
            *self.bottom.read_outgoing_elements(self.model, source),
            *self.bottom.read_outgoing_elements(self.model, target),
        )  # create assoc edge
        self.bottom.create_edge(self.model, assoc_edge, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Association")  # retrieve type
        self.bottom.create_edge(assoc_edge, scd_node, "Morphism")  # create morphism link
        if src_min_c is not None:
            set_cardinality("source_lower", src_min_c)
        if src_max_c is not None:
            set_cardinality("source_upper", src_max_c)
        if tgt_min_c is not None:
            set_cardinality("target_lower", tgt_min_c)
        if tgt_max_c is not None:
            set_cardinality("target_upper", tgt_max_c)

    def create_global_constraint(self, name: str):
        # create element + morphism links
        element_node = self.bottom.create_node()  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "GlobalConstraint")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link

    def create_attribute(self, name: str):
        # create element + morphism links
        element_node = self.bottom.create_node()  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Attribute")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link

    def create_attribute_link(self, source: str, target: str, name: str, optional: bool):
        # create attribute link + morphism links
        assoc_edge = self.bottom.create_edge(
            *self.bottom.read_outgoing_elements(self.model, source),
            *self.bottom.read_outgoing_elements(self.model, target),
        )  # create inheritance edge
        self.bottom.create_edge(self.model, assoc_edge, f"{source}_{name}")  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink")  # retrieve type
        self.bottom.create_edge(assoc_edge, scd_node, "Morphism")  # create morphism link
        # name attribute
        name_model = self.bottom.create_node()
        String(name_model, self.bottom.state).create(name)
        name_node = self.bottom.create_node(str(name_model))
        self.bottom.create_edge(self.model, name_node, f"{source}_{name}.name")
        name_link = self.bottom.create_edge(assoc_edge, name_node)
        self.bottom.create_edge(self.model, name_link, f"{source}_{name}.name_link")
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "String")
        scd_link, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink_name")
        self.bottom.create_edge(name_node, scd_node, "Morphism")
        self.bottom.create_edge(name_link, scd_link, "Morphism")
        # optional attribute
        optional_model = self.bottom.create_node()
        Boolean(optional_model, self.bottom.state).create(optional)
        optional_node = self.bottom.create_node(str(optional_model))
        self.bottom.create_edge(self.model, optional_node, f"{source}_{name}.optional")
        optional_link = self.bottom.create_edge(assoc_edge, optional_node)
        self.bottom.create_edge(self.model, optional_link, f"{source}_{name}.optional_link")
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Boolean")
        scd_link, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink_optional")
        self.bottom.create_edge(optional_node, scd_node, "Morphism")
        self.bottom.create_edge(optional_link, scd_link, "Morphism")

    def create_model_ref(self, name: str, model: UUID):
        # create element + morphism links
        element_node = self.bottom.create_node(str(model))  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link

    def create_inheritance(self, child: str, parent: str):
        # create inheritance + morphism links
        assoc_edge = self.bottom.create_edge(
            *self.bottom.read_outgoing_elements(self.model, child),
            *self.bottom.read_outgoing_elements(self.model, parent),
        )  # create inheritance edge
        self.bottom.create_edge(self.model, assoc_edge, f"{child}_inh_{parent}")  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")  # retrieve type
        self.bottom.create_edge(assoc_edge, scd_node, "Morphism")  # create morphism link

    def add_constraint(self, element: str, code: str):
        element_node, = self.bottom.read_outgoing_elements(self.model, element)  # retrieve element
        # code attribute
        code_node = self.bottom.create_node(code)
        self.bottom.create_edge(self.model, code_node, f"{element}.constraint")
        code_link = self.bottom.create_edge(element_node, code_node)
        self.bottom.create_edge(self.model, code_link, f"{element}.constraint_link")
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "ActionCode")
        scd_link, = self.bottom.read_outgoing_elements(self.scd_model, "Element_constraint")
        self.bottom.create_edge(code_node, scd_node, "Morphism")
        self.bottom.create_edge(code_link, scd_link, "Morphism")

    def list_elements(self):
        scd_names = {}
        for key in self.bottom.read_keys(self.scd_model):
            element, = self.bottom.read_outgoing_elements(self.scd_model, key)
            scd_names[element] = key
        unsorted = []
        for key in self.bottom.read_keys(self.model):
            element, = self.bottom.read_outgoing_elements(self.model, key)
            element_types = self.bottom.read_outgoing_elements(element, "Morphism")
            type_model_elements = self.bottom.read_outgoing_elements(self.scd_model)
            element_type_node, = [e for e in element_types if e in type_model_elements]
            unsorted.append((key, scd_names[element_type_node]))
        for elem in sorted(unsorted, key=lambda e: e[0]):
            print("{} : {}".format(*elem))

    def delete_element(self, name: str):
        keys = self.bottom.read_keys(self.model)
        r = re.compile(r"{}\..*".format(name))
        to_delete = list(filter(r.match, keys))
        for key in to_delete:
            # TODO: find way to solve memory leak, primitive models are not deleted this way
            node, = self.bottom.read_outgoing_elements(self.model, label=key)
            self.bottom.delete_element(node)


if __name__ == '__main__':
    from state.devstate import DevState as State
    s = State()
    from bootstrap.scd import bootstrap_scd
    scd = bootstrap_scd(s)
    int_type_id = s.read_dict(s.read_root(), "Integer")
    int_type = UUID(s.read_value(int_type_id))
    service = SCD(scd, s.create_node(), s)
    service.create_class("Place")
    service.create_class("Transition")
    service.create_association("P2T", "Place", "Transition")
    service.create_association("T2P", "Transition", "Place")
    service.create_model_ref("Integer", int_type)
    service.create_attribute_link("Place", "Integer", "tokens", False)
    service.create_attribute_link("P2T", "Integer", "weight", False)
    service.create_attribute_link("T2P", "Integer", "weight", False)
    service.list_elements()
