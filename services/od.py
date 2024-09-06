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

    def get_class_of_object(self, object_name: str):
        object_node, = self.bottom.read_outgoing_elements(self.model, object_name) # get the object
        type_el, = self.bottom.read_outgoing_elements(object_node, "Morphism")
        for key in self.bottom.read_keys(self.type_model):
            type_el2, = self.bottom.read_outgoing_elements(self.type_model, key)
            if type_el == type_el2:
                return key

    def create_slot(self, attr_name: str, object_name: str, target_name: str):
        class_name = self.get_class_of_object(object_name)
        attr_link_name = f"{class_name}_{attr_name}"
        # An attribute-link is indistinguishable from an ordinary link:
        return self.create_link(attr_link_name, object_name, target_name)

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
        scd_node, = self.bottom.read_outgoing_elements(self.type_model, type_name)  # retrieve type
        self.bottom.create_edge(element_node, scd_node, "Morphism")  # create morphism link


    def create_link(self, assoc_name: str, src_obj_name: str, tgt_obj_name: str):
        print(tgt_obj_name)
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

