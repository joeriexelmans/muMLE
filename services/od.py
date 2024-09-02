from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from services.primitives.string_type import String

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
        if len(abstract_nodes) == 1:
            is_abstract = self.bottom.read_value(abstract_node)
        else:
            # 'abstract' is optional attribute, default is False
            is_abstract = False

        print("class", name, "is abstract?", is_abstract)

        if is_abstract:
            raise Exception("Cannot instantiate abstract class!")

        object_node = self.bottom.create_node()
        self.bottom.create_edge(self.model, object_node, name) # attach to model
        self.bottom.create_edge(object_node, class_node, "Morphism") # typed-by link

        return object_node


    def create_slot(self, object_name: str, attr_name: str, value: UUID):
        attr_node = self.bottom.read_outgoing_elements(self.type_model, attr_name) # get the attribute
        object_node, = self.bottom.read_outgoing_elements(self.model, object_name) # get the object
        slot_node = value

        # generate a unique name for the slot
        i = 0;
        while len(self.bottom.read_outgoing_elements(self.model, f"{object_name}.{attr_name}{i}")) != 0:
            i += 1

        self.bottom.create_edge(self.model, slot_node, f"{object_name}.{attr_name}{i}") # attach to model root
        slot_link = self.bottom.create_edge(object_node, slot_node) # attach to object
        self.bottom.create_edge(self.model, slot_link, f"{object_name}.{attr_name}{i}_link") # attach attr-link to model

        self.bottom.create_edge(slot_node, attr_node, "Morphism") # slot typed-by attribute
        slot_link_type, = self.bottom.read_outgoing_elements(self.type_model, "AttributeLink")
        self.bottom.create_edge(slot_link, slot_link_type)


    def create_link(self, assoc_name: str, src_obj_name: str, tgt_obj_name: str):
        src_obj_node, = self.bottom.read_outgoing_elements(self.model, src_obj_name)
        tgt_obj_node, = self.bottom.read_outgoing_elements(self.model, tgt_obj_name)

        link_edge = self.bottom.create_edge(src_obj_node, tgt_obj_node);

        # generate a unique name for the link
        i = 0;
        while True:
            link_name = f"{assoc_name}{i}"
            if len(self.bottom.read_outgoing_elements(self.model, link_name)) == 0:
                break
            i += 1

        self.bottom.create_edge(self.model, link_edge, link_name)

        type_edge, = self.bottom.read_outgoing_elements(self.type_model, assoc_name)
        self.bottom.create_edge(link_edge, type_edge, "Morphism")

