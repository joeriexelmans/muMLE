from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.boolean_type import Boolean
from services.primitives.integer_type import Integer
from services.primitives.string_type import String

import re


class SCD:
    """
    Implements services for the simple class diagrams LTM.
    Implementation is done in terms of services provided by LTM-bottom
    """
    def __init__(self, model: UUID, state: State):
        type_model_id = state.read_dict(state.read_root(), "SCD")
        self.scd_model = UUID(state.read_value(type_model_id))
        self.model = model
        self.bottom = Bottom(state)

    def create_class(self, name: str, abstract: bool = None, min_c: int = None, max_c: int = None):
        """
        Creates an instance of a class.

        Args:
            name: the name of the class to be created
            abstract: indicates whether or not the class is an abstract class
            min_c: lower bound for class multicplicity
            max_c: upper bound for class multicplicity

        Returns:
            Nothing.
        """
        
        def set_cardinality(bound: str, value: int):
            """ Helper for setting cardinality attributes """
            # Create cardinality attribute root node
            # Do note that this is an instance of a ModelRef!
            _c_model = self.bottom.create_node()
            Integer(_c_model, self.bottom.state).create(value)
            _c_node = self.bottom.create_node(str(_c_model))  # store UUID of primitive value model
            self.bottom.create_edge(self.model, _c_node, f"{name}.{bound}_cardinality")  # link to model root
            _c_link = self.bottom.create_edge(class_node, _c_node)  # link class to attribute
            self.bottom.create_edge(self.model, _c_link, f"{name}.{bound}_cardinality_link")  # link attr link to model root
            # retrieve types from metamodel
            _scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Integer")
            _scd_link, = self.bottom.read_outgoing_elements(self.scd_model, f"Class_{bound}_cardinality")
            # type newly created elements
            self.bottom.create_edge(_c_node, _scd_node, "Morphism")
            self.bottom.create_edge(_c_link, _scd_link, "Morphism")
        
        # create class + attributes + morphism links
        class_node = self.bottom.create_node()  # create class node
        self.bottom.create_edge(self.model, class_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Class")  # retrieve type
        self.bottom.create_edge(class_node, scd_node, "Morphism")  # create morphism link
        if abstract is not None:
            # operations similar to set_cardinality function defined above
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
            set_cardinality("upper", max_c)

    def create_association(self, name: str, source: str, target: str,
                           src_min_c: int = None, src_max_c: int = None,
                           tgt_min_c: int = None, tgt_max_c: int = None):
        """
        Creates an instance of an association.

        Args:
            name: the name of the association to be created
            source: the name of the source of the association
            target: the name of the target of the association
            src_min_c: lower bound for source multicplicity
            src_max_c: upper bound for source multicplicity
            tgt_min_c: lower bound for target multicplicity
            tgt_max_c: upper bound for target multicplicity

        Returns:
            Nothing.
        """
        src, = self.bottom.read_outgoing_elements(self.model, source)
        tgt, = self.bottom.read_outgoing_elements(self.model, target)
        return self._create_association(name, src, tgt,
            src_min_c, src_max_c,
            tgt_min_c, tgt_max_c)

    def _create_association(self, name: str, source: UUID, target: UUID,
                           src_min_c: int = None, src_max_c: int = None,
                           tgt_min_c: int = None, tgt_max_c: int = None):

        def set_cardinality(bound: str, value: int):
            # similar to set_cardinality function defined in create_class
            _c_model = self.bottom.create_node()
            Integer(_c_model, self.bottom.state).create(value)
            _c_node = self.bottom.create_node(str(_c_model))
            self.bottom.create_edge(self.model, _c_node, f"{name}.{bound}_cardinality")
            _c_link = self.bottom.create_edge(assoc_edge, _c_node)
            self.bottom.create_edge(self.model, _c_link, f"{name}.{bound}_cardinality_link")
            _scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Integer")
            _scd_link, = self.bottom.read_outgoing_elements(self.scd_model, f"Association_{bound}_cardinality")
            self.bottom.create_edge(_c_node, _scd_node, "Morphism")
            self.bottom.create_edge(_c_link, _scd_link, "Morphism")

        # create association + attributes + morphism links
        assoc_edge = self.bottom.create_edge(source, target)  # create assoc edge
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
        """
        Defines a global constraint element.

        Args:
            name: the name of the global constraint to be created

        Returns:
            Nothing.
        """
        # create element + morphism links
        element_node = self.bottom.create_node()  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "GlobalConstraint")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link

    def create_attribute(self, name: str):
        """
        Defines an attribute element.

        Args:
            name: the name of the attribute to be created

        Returns:
            Nothing.
        """
        # create element + morphism links
        element_node = self.bottom.create_node()  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Attribute")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link

    def create_attribute_link(self, source: str, target: str, name: str, optional: bool):
        """
        Defines an attribute link element.

        Args:
            source: element attribute will be attached to
            target: attribute element
            name: name of the attribute
            optional: indicates whether attribute is optional

        Returns:
            Nothing.
        """
        tgt, = self.bottom.read_outgoing_elements(self.model, target)
        return self._create_attribute_link(source, tgt, name, optional)

    def _create_attribute_link(self, source: str, target: UUID, name: str, optional: bool):
        # create attribute link + morphism links
        src, = self.bottom.read_outgoing_elements(self.model, source)
        assoc_edge = self.bottom.create_edge(src, target)  # create v edge
        self.bottom.create_edge(self.model, assoc_edge, f"{source}_{name}")  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink")  # retrieve type
        self.bottom.create_edge(assoc_edge, scd_node, "Morphism")  # create morphism link
        # name attribute
        # Do note that this is an instance of a ModelRef!
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
        # Do note that this is an instance of a ModelRef!
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
        """
        Defines a model ref element.

        Args:
            name: name of the model ref
            model: uuid of the external model

        Returns:
            Nothing.
        """
        # create element + morphism links
        element_node = self.bottom.create_node(str(model))  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "ModelRef")  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link
        return element_node

    def create_inheritance(self, child: str, parent: str):
        """
        Defines an inheritance link element.

        Args:
            child: child element of the inheritance relationship
            parent: parent element of the inheritance relationship

        Returns:
            Nothing.
        """
        c, = self.bottom.read_outgoing_elements(self.model, child)
        p, = self.bottom.read_outgoing_elements(self.model, parent)
        return self._create_inheritance(c, p)


    def _create_inheritance(self, child: UUID, parent: UUID):
        # create inheritance + morphism links
        inh_edge = self.bottom.create_edge(child, parent)
        child_name = self.get_class_name(child)
        parent_name = self.get_class_name(parent)
        self.bottom.create_edge(self.model, inh_edge, f"{child_name}_inh_{parent_name}")  # attach to model
        scd_node, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")  # retrieve type
        self.bottom.create_edge(inh_edge, scd_node, "Morphism")  # create morphism link

    def get_class_name(self, cls: UUID):
        for key in self.bottom.read_keys(self.model):
            el, = self.bottom.read_outgoing_elements(self.model, key)
            if el == cls:
                return key

    def add_constraint(self, element: str, code: str):
        """
        Defines a constraint on an element.

        Args:
            element: element the constraint is attached to
            code: constraint code

        Returns:
            Nothing.
        """
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
        """
        Lists elements in the model.

        Returns:
            A list of elements in alphabetical order.
        """
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
            unsorted.append(f"{key} : {scd_names[element_type_node]}")
        return sorted(unsorted)

    def get_classes(self):
        class_node, = self.bottom.read_outgoing_elements(self.scd_model, "Class")
        return self.get_typed_by(class_node)

    def get_associations(self):
        assoc_node, = self.bottom.read_outgoing_elements(self.scd_model, "Association")
        return self.get_typed_by(assoc_node)

    def get_inheritances(self):
        inh_node, = self.bottom.read_outgoing_elements(self.scd_model, "Inheritance")
        return self.get_typed_by(inh_node)

    def get_typed_by(self, type_node: UUID):
        name_to_instance = {}
        for key in self.bottom.read_keys(self.model):
            element, = self.bottom.read_outgoing_elements(self.model, key)
            element_types = self.bottom.read_outgoing_elements(element, "Morphism")
            if type_node in element_types:
                name_to_instance[key] = element
        # mapping from instance name to UUID
        return name_to_instance


    def get_attributes(self, class_name: str):
        attr_link_node, = self.bottom.read_outgoing_elements(self.scd_model, "AttributeLink")
        class_node, = self.bottom.read_outgoing_elements(self.model, class_name)
        name_to_attr = {}
        for edge in self.bottom.read_outgoing_edges(class_node):
            edge_types = self.bottom.read_outgoing_elements(edge, "Morphism")
            if attr_link_node in edge_types:
                name_to_attr[key] = edge
        return name_to_attr

    def delete_element(self, name: str):
        """
        Deletes an element from the model.

        Args:
            name: name of the element to delete

        Returns:
            Nothing.
        """
        keys = self.bottom.read_keys(self.model)
        r = re.compile(r"{}\..*".format(name))
        to_delete = list(filter(r.match, keys))
        for key in to_delete:
            # TODO: find way to solve memory leak, primitive models are not deleted this way
            node, = self.bottom.read_outgoing_elements(self.model, label=key)
            self.bottom.delete_element(node)

    def to_bottom(self):
        # already implemented in terms of LTM bottom
        pass

    def from_bottom(self):
        # already implemented in terms of LTM bottom
        pass


if __name__ == '__main__':
    from state.devstate import DevState as State
    s = State()
    from bootstrap.scd import bootstrap_scd
    scd = bootstrap_scd(s)
    # Retrieve refs to primitive type models
    # # integer
    int_type_id = s.read_dict(s.read_root(), "Integer")
    int_type = UUID(s.read_value(int_type_id))
    print(f"Integer Model UUID: {int_type}")  # 6
    # # string
    str_type_id = s.read_dict(s.read_root(), "String")
    str_type = UUID(s.read_value(str_type_id))
    print(f"String Model UUID: {str_type}")  # 16
    # Create LTM_PN
    model_uuid = s.create_node()
    print(f"LTM_PN Model UUID: {model_uuid}")  # 845
    service = SCD(model_uuid, s)
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
