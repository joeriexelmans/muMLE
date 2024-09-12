from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from services.primitives.string_type import String
from services.primitives.boolean_type import Boolean
from typing import Optional

def get_attr_link_name(class_name: str, attr_name: str):
    return f"{class_name}_{attr_name}"

# Object Diagrams service

class OD:

    def __init__(self, type_model: UUID, model: UUID, state: State):
        """
        Implements services for the object diagrams LTM.
        Implementation is done in terms of services provided by LTM-bottom.

            Args:
                type_model: The SCD-conforming class diagram that contains the types of this object diagram
                model: UUID of the (OD) model to manipulate
        """

        self.type_model = type_model
        self.model = model
        self.bottom = Bottom(state)


    def create_object(self, name: str, class_name: str):
        class_node, = self.bottom.read_outgoing_elements(self.type_model, class_name)
        abstract_nodes = self.bottom.read_outgoing_elements(self.type_model, f"{class_name}.abstract")
        return self._create_object(name, class_node)

    def _create_object(self, name: str, class_node: UUID):
        # Look at our `type_model` as if it's an object diagram:
        mm_od = OD(
            get_scd_mm(self.bottom), # the type model of our type model
            self.type_model,
            self.bottom.state)
        # # Read the 'abstract' slot of the class
        abstract_slot = mm_od.get_slot(class_node, "abstract")
        print('abstract_slot:', abstract_slot)
        if abstract_slot != None:
            is_abstract = Boolean(abstract_slot, self.bottom.state).read()
        else:
            is_abstract = False

        if is_abstract:
            raise Exception("Cannot instantiate abstract class!")

        object_node = self.bottom.create_node()
        self.bottom.create_edge(self.model, object_node, name) # attach to model
        self.bottom.create_edge(object_node, class_node, "Morphism") # typed-by link

        return object_node

    def get_class_of_object(self, object_name: str):
        object_node, = self.bottom.read_outgoing_elements(self.model, object_name) # get the object
        return self._get_class_of_object(object_node)


    def _get_class_of_object(self, object_node: UUID):
        type_el, = self.bottom.read_outgoing_elements(object_node, "Morphism")
        for key in self.bottom.read_keys(self.type_model):
            type_el2, = self.bottom.read_outgoing_elements(self.type_model, key)
            if type_el == type_el2:
                return key

    def create_slot(self, attr_name: str, object_name: str, target_name: str):
        class_name = self.get_class_of_object(object_name)
        attr_link_name = get_attr_link_name(class_name, attr_name)
        print('attr_link_name:', attr_link_name)
        # An attribute-link is indistinguishable from an ordinary link:
        return self.create_link(
            get_attr_link_name(object_name, attr_name),
            attr_link_name, object_name, target_name)

    def get_slot(self, object_node: UUID, attr_name: str):
        # I really don't like how complex and inefficient it is to read an attribute of an object...
        class_name = self._get_class_of_object(object_node)
        attr_link_name = get_attr_link_name(class_name, attr_name)
        print(attr_link_name)
        type_edge, = self.bottom.read_outgoing_elements(self.type_model, attr_link_name)
        for outgoing_edge in self.bottom.read_outgoing_edges(object_node):
            if type_edge in self.bottom.read_outgoing_elements(outgoing_edge, "Morphism"):
                slot_ref = self.bottom.read_edge_target(outgoing_edge)
                slot_node = UUID(self.bottom.read_value(slot_ref))
                return slot_node

    def create_integer_value(self, name: str, value: int):
        from services.primitives.integer_type import Integer
        int_node = self.bottom.create_node()
        integer_t = Integer(int_node, self.bottom.state)
        integer_t.create(value)
        # name = 'int'+str(value) # name of the ref to the created integer
        # By convention, the type model must have a ModelRef named "Integer"
        self.create_model_ref(name, "Integer", int_node)
        return name

    def create_string_value(self, name: str, value: str):
        from services.primitives.string_type import String
        string_node = self.bottom.create_node()
        string_t = String(string_node, self.bottom.state)
        string_t.create(value)
        # name = 'str-'+value # name of the ref to the created integer
        # By convention, the type model must have a ModelRef named "Integer"
        self.create_model_ref(name, "String", string_node)
        return name

    # Identical to the same SCD method:
    def create_model_ref(self, name: str, type_name: str, model: UUID):
        # create element + morphism links
        element_node = self.bottom.create_node(str(model))  # create element node
        self.bottom.create_edge(self.model, element_node, name)  # attach to model
        type_node, = self.bottom.read_outgoing_elements(self.type_model, type_name)  # retrieve type
        self.bottom.create_edge(element_node, type_node, "Morphism")  # create morphism link


    def create_link(self, link_name: Optional[str], assoc_name: str, src_obj_name: str, tgt_obj_name: str):
        src_obj_node, = self.bottom.read_outgoing_elements(self.model, src_obj_name)
        tgt_obj_node, = self.bottom.read_outgoing_elements(self.model, tgt_obj_name)

        # generate a unique name for the link
        if link_name == None:
            i = 0;
            while True:
                link_name = f"{assoc_name}{i}"
                if len(self.bottom.read_outgoing_elements(self.model, link_name)) == 0:
                    break
                i += 1
        print('link_name:', link_name)

        type_edge, = self.bottom.read_outgoing_elements(self.type_model, assoc_name)

        return self._create_link(link_name, type_edge, src_obj_node, tgt_obj_node)

    def _create_link(self, link_name: str, type_edge: str, src_obj_node: UUID, tgt_obj_node: UUID):
        # the link itself is unlabeled:
        link_edge = self.bottom.create_edge(src_obj_node, tgt_obj_node)
        # it is only in the context of the model, that the link has a name:
        self.bottom.create_edge(self.model, link_edge, link_name) # add to model
        self.bottom.create_edge(link_edge, type_edge, "Morphism")
        return link_edge

def get_types(bottom: Bottom, obj: UUID):
    return bottom.read_outgoing_elements(obj, "Morphism")

def get_type(bottom: Bottom, obj: UUID):
    types = get_types(bottom, obj)
    if len(types) == 1:
        return types[0]
    elif len(types) > 1:
        raise Exception(f"Expected at most one type. Instead got {len(types)}.")

def is_typed_by(bottom, el: UUID, typ: UUID):
    for typed_by in get_types(bottom, el):
        if typed_by == typ:
            return True
    return False

def get_scd_mm(bottom):
    scd_metamodel_id = bottom.state.read_dict(bottom.state.read_root(), "SCD")
    scd_metamodel = UUID(bottom.state.read_value(scd_metamodel_id))
    return scd_metamodel    

def get_scd_mm_class_node(bottom: Bottom):
    return get_scd_mm_node(bottom, "Class")

def get_scd_mm_attributelink_node(bottom: Bottom):
    return get_scd_mm_node(bottom, "AttributeLink")

def get_scd_mm_assoc_node(bottom: Bottom):
    return get_scd_mm_node(bottom, "Association")

def get_scd_mm_modelref_node(bottom: Bottom):
    return get_scd_mm_node(bottom, "ModelRef")

def get_scd_mm_node(bottom: Bottom, node_name: str):
    scd_metamodel = get_scd_mm(bottom)
    node, = bottom.read_outgoing_elements(scd_metamodel, node_name)
    return node

def get_object_name(bottom: Bottom, model: UUID, object_node: UUID):
    for key in bottom.read_keys(model):
        for el in bottom.read_outgoing_elements(model, key):
            if el == object_node:
                return key
