from services import od
from api import cd
from services.bottom.V0 import Bottom
from uuid import UUID
from typing import Optional

NEXT_ID = 0

# Models map names to elements
# This builds the inverse mapping, so we can quickly lookup the name of an element
def build_name_mapping(state, m):
    mapping = {}
    bottom = Bottom(state)
    for name in bottom.read_keys(m):
        element, = bottom.read_outgoing_elements(m, name)
        mapping[element] = name
    return mapping

# Object Diagram API
# Intended to replace the 'services.od.OD' class eventually
class ODAPI:
    def __init__(self, state, m: UUID, mm: UUID):
        self.state = state
        self.bottom = Bottom(state)
        self.m = m
        self.mm = mm
        self.od = od.OD(mm, m, state)
        self.cd = cd.CDAPI(state, mm)

        self.create_boolean_value = self.od.create_boolean_value
        self.create_integer_value = self.od.create_integer_value
        self.create_string_value = self.od.create_string_value
        self.create_actioncode_value = self.od.create_actioncode_value

        self.__recompute_mappings()

    # Called after every change - makes querying faster but modifying slower
    def __recompute_mappings(self):
        self.obj_to_name = {**build_name_mapping(self.state, self.m), **build_name_mapping(self.state, self.mm)}
        # self.obj_to_type = {}
        self.type_to_objs = { type_name : set() for type_name in self.bottom.read_keys(self.mm)}
        for m_name in self.bottom.read_keys(self.m):
            m_element, = self.bottom.read_outgoing_elements(self.m, m_name)
            tm_element = self.get_type(m_element)
            tm_name = self.obj_to_name[tm_element]
            # self.obj_to_type[m_name] = tm_name
            self.type_to_objs[tm_name].add(m_name)

    def get_value(self, obj: UUID):
        return od.read_primitive_value(self.bottom, obj, self.mm)[0]

    def get_target(self, link: UUID):
        return self.bottom.read_edge_target(link)

    def get_source(self, link: UUID):
        return self.bottom.read_edge_source(link)

    def get_slot(self, obj: UUID, attr_name: str):
        return self.od.get_slot(obj, attr_name)

    def get_slot_link(self, obj: UUID, attr_name: str):
        return self.od.get_slot_link(obj, attr_name)

    def get_outgoing(self, obj: UUID, assoc_name: str):
        return od.find_outgoing_typed_by(self.bottom, src=obj, type_node=self.bottom.read_outgoing_elements(self.mm, assoc_name)[0])

    def get_incoming(self, obj: UUID, assoc_name: str):
        return od.find_incoming_typed_by(self.bottom, tgt=obj, type_node=self.bottom.read_outgoing_elements(self.mm, assoc_name)[0])

    def get_all_instances(self, type_name: str, include_subtypes=True):
        obj_names = self.type_to_objs[type_name]
        return [(obj_name, self.bottom.read_outgoing_elements(self.m, obj_name)[0]) for obj_name in obj_names]

    def get_type(self, obj: UUID):
        types = self.bottom.read_outgoing_elements(obj, "Morphism")
        if len(types) != 1:
            raise Exception(f"Expected obj to have 1 type, instead got {len(types)} types.")
        return types[0]

    def get_name(self, obj: UUID):
        return (
            [name for name in self.bottom.read_keys(self.m) if self.bottom.read_outgoing_elements(self.m, name)[0] == obj] +
            [name for name in self.bottom.read_keys(self.mm) if self.bottom.read_outgoing_elements(self.mm, name)[0] == obj]
        )[0]
        return self.obj_to_name[obj]

    def get(self, name: str):
        return self.bottom.read_outgoing_elements(self.m, name)[0]

    def get_type_name(self, obj: UUID):
        return self.get_name(self.get_type(obj))

    def is_instance(obj: UUID, type_name: str, include_subtypes=True):
        typ = self.cd.get_type(type_name)
        types = set(typ) if not include_subtypes else self.cd.transitive_subtypes[type_name]
        for type_of_obj in self.bottom.read_outgoing_elements(obj, "Morphism"):
            if type_of_obj in types:
                return True
        return False

    def delete(self, obj: UUID):
        self.bottom.delete_element(obj)
        self.__recompute_mappings()

    def get_slot_value(self, obj: UUID, attr_name: str):
        return self.get_value(self.get_slot(obj, attr_name))

    def set_slot_value(self, obj: UUID, attr_name: str, new_value: any):
        obj_name = self.get_name(obj)

        link_name = f"{obj_name}_{attr_name}"
        target_name = f"{obj_name}.{attr_name}"

        old_slot_link = self.get_slot_link(obj, attr_name)
        if old_slot_link != None:
            old_target = self.get_target(old_slot_link)
            # if old_target != None:
            self.bottom.delete_element(old_target) # this also deletes the slot-link

        new_target = self.create_primitive_value(target_name, new_value)
        slot_type = self.cd.find_attribute_type(self.get_type_name(obj), attr_name)
        new_link = self.od._create_link(link_name, slot_type, obj, new_target)
        self.__recompute_mappings()

    def create_primitive_value(self, name: str, value: any, is_code=False):
        if isinstance(value, bool):
            tgt = self.create_boolean_value(name, value)
        elif isinstance(value, int):
            tgt = self.create_integer_value(name, value)
        elif isinstance(value, str):
            if is_code:
                tgt = self.create_actioncode_value(name, value)
            else:
                tgt = self.create_string_value(name, value)
        else:
            raise Exception("Unimplemented type "+value)
        self.__recompute_mappings()
        return tgt

    def create_link(self, link_name: Optional[str], assoc_name: str, src: UUID, tgt: UUID):
        global NEXT_ID
        typ, = self.bottom.read_outgoing_elements(self.mm, assoc_name)
        if link_name == None:
            link_name = f"__{assoc_name}{NEXT_ID}"
            NEXT_ID += 1
        link_id = self.od._create_link(link_name, typ, src, tgt)
        self.__recompute_mappings()
        return link_id