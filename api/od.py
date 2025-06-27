from services import od
from api import cd
from services.bottom.V0 import Bottom
from services.primitives.boolean_type import Boolean
from services.primitives.integer_type import Integer
from services.primitives.string_type import String
from services.primitives.actioncode_type import ActionCode
from uuid import UUID
from typing import Optional, Any

NEXT_ID = 0

# Models map names to elements
# This builds the inverse mapping, so we can quickly lookup the name of an element
def build_name_mapping(state, m):
    mapping = {}
    bottom = Bottom(state)
    for name in bottom.read_keys(m):
        elements = bottom.read_outgoing_elements(m, name)
        if len(elements) > 1:
            print(f"Warning: more than one element with name '{name}'")
        mapping[elements[0]] = name
    return mapping

class NoSuchSlotException(Exception):
    pass

# Object Diagram API
# Intended to replace the 'services.od.OD' class eventually
class ODAPI:
    def __init__(self, state, m: UUID, mm: UUID):
        self.state = state
        self.bottom = Bottom(state)
        self.m = m
        self.mm = mm
        self.od = od.OD(mm, m, state)
        self.cdapi = cd.CDAPI(state, mm)

        self.create_boolean_value = self.od.create_boolean_value
        self.create_integer_value = self.od.create_integer_value
        self.create_string_value = self.od.create_string_value
        self.create_actioncode_value = self.od.create_actioncode_value

        self.recompute_mappings()

    # Called after every change - makes querying faster but modifying slower
    def recompute_mappings(self):
        self.m_obj_to_name = build_name_mapping(self.state, self.m)
        self.mm_obj_to_name = build_name_mapping(self.state, self.mm)
        self.type_to_objs = { type_name : set() for type_name in self.bottom.read_keys(self.mm)}
        for m_name in self.bottom.read_keys(self.m):
            m_element, = self.bottom.read_outgoing_elements(self.m, m_name)
            tm_element = self.get_type(m_element)
            if tm_element in self.mm_obj_to_name:
                tm_name = self.mm_obj_to_name[tm_element]
                # self.obj_to_type[m_name] = tm_name
                self.type_to_objs[tm_name].add(m_name)

    def get_value(self, obj: UUID):
        return od.read_primitive_value(self.bottom, obj, self.mm)[0]

    def get_target(self, link: UUID) -> UUID:
        return self.bottom.read_edge_target(link)

    def get_source(self, link: UUID) -> UUID:
        return self.bottom.read_edge_source(link)

    def get_slot(self, obj: UUID, attr_name: str) -> UUID:
        slot = self.od.get_slot(obj, attr_name)
        if slot == None:
            raise NoSuchSlotException(f"Object '{self.m_obj_to_name[obj]}' has no slot '{attr_name}'")
        return slot

    def get_slot_link(self, obj: UUID, attr_name: str) -> UUID:
        return self.od.get_slot_link(obj, attr_name)

    # Parameter 'include_subtypes': whether to include subtypes of the given association
    def get_outgoing(self, obj: UUID, assoc_name: str, include_subtypes=True) -> list[UUID]:
        outgoing = self.bottom.read_outgoing_edges(obj)
        return self.filter_edges_by_type(outgoing, assoc_name, include_subtypes)

    # Parameter 'include_subtypes': whether to include subtypes of the given association
    def get_incoming(self, obj: UUID, assoc_name: str, include_subtypes=True):
        incoming = self.bottom.read_incoming_edges(obj)
        return self.filter_edges_by_type(incoming, assoc_name, include_subtypes)

    def filter_edges_by_type(self, outgoing: list[UUID], assoc_name: str, include_subtypes=True) -> list[UUID]:
        result: list[UUID] = []
        for o in outgoing:
            try:
                type_of_outgoing_link = self.get_type_name(o)
            except:
                continue # OK, not all edges are typed
            if (include_subtypes and self.cdapi.is_subtype(super_type_name=assoc_name, sub_type_name=type_of_outgoing_link)
                or not include_subtypes and type_of_outgoing_link == assoc_name):
                    result.append(o)
        return result

    # Returns list of tuples (name, obj)
    def get_all_instances(self, type_name: str, include_subtypes=True) -> list[UUID]:
        if include_subtypes:
            all_types = self.cdapi.transitive_sub_types[type_name]
        else:
            all_types = set([type_name])
        obj_names = [obj_name for type_name in all_types for obj_name in self.type_to_objs[type_name]]
        return [(obj_name, self.bottom.read_outgoing_elements(self.m, obj_name)[0]) for obj_name in obj_names]

    def get_type(self, obj: UUID):
        types = self.bottom.read_outgoing_elements(obj, "Morphism")
        if len(types) != 1:
            raise Exception(f"Expected obj to have 1 type, instead got {len(types)} types.")
        return types[0]

    def get_name(self, obj: UUID):
        if obj in self.m_obj_to_name:
            return self.m_obj_to_name[obj]
        elif obj in self.mm_obj_to_name:
            return self.mm_obj_to_name[obj]
        else:
            raise Exception(f"Couldn't find name of {obj} - are you sure it exists in the (meta-)model?")

    def get(self, name: str) -> UUID:
        results = self.bottom.read_outgoing_elements(self.m, name)
        if len(results) == 1:
            return results[0]
        elif len(results) >= 2:
            raise Exception("this should never happen")
        else:
            raise Exception(f"No such element in model: '{name}'")

    def get_type_name(self, obj: UUID) -> str:
        return self.get_name(self.get_type(obj))

    def is_instance(self, obj: UUID, type_name: str, include_subtypes=True) -> bool:
        typ = self.cdapi.get_type(type_name)
        types = set(typ) if not include_subtypes else self.cdapi.transitive_sub_types[type_name]
        for type_of_obj in self.bottom.read_outgoing_elements(obj, "Morphism"):
            if self.get_name(type_of_obj) in types:
                return True
        return False

    def delete(self, obj: UUID) -> None:
        self.bottom.delete_element(obj)
        self.recompute_mappings()

    # Does the the object have the given attribute?
    def has_slot(self, obj: UUID, attr_name: str) -> bool:
        class_name = self.get_name(self.get_type(obj))
        if self.od.get_attr_link_name(class_name, attr_name) is None:
            return False
        return self.od.get_slot_link(obj, attr_name) is not None

    def get_slots(self, obj: UUID) -> list[str]:
        return [attr_name for attr_name, _ in self.od.get_slots(obj)]

    def get_slot_value(self, obj: UUID, attr_name: str) -> Any:
        slot = self.get_slot(obj, attr_name)
        return self.get_value(slot)

    # does the given slot contain code?
    # this complements `get_slot_value` which will return code as a string
    def slot_has_code(self, obj: UUID, attr_name: str):
        slot = self.get_slot(obj, attr_name)
        return self.get_type_name(slot) == "ActionCode"

    # Returns the given default value if the slot does not exist on the object.
    # The attribute must exist in the object's class, or an exception will be thrown.
    # The slot may not exist however, if the attribute is defined as 'optional' in the class.
    def get_slot_value_default(self, obj: UUID, attr_name: str, default: any) -> any:
        try:
            return self.get_slot_value(obj, attr_name)
        except NoSuchSlotException:
            return default

    # create or update slot value
    def set_slot_value(self, obj: UUID, attr_name: str, new_value: any, is_code=False) -> None:
        obj_name = self.get_name(obj)

        link_name = f"{obj_name}_{attr_name}"
        target_name = f"{obj_name}.{attr_name}"

        old_slot_link = self.get_slot_link(obj, attr_name)
        if old_slot_link != None:
            old_target = self.get_target(old_slot_link)
            # if old_target != None:
            self.bottom.delete_element(old_target) # this also deletes the slot-link

        new_target = self.create_primitive_value(target_name, new_value, is_code)
        slot_type = self.cdapi.find_attribute_type(self.get_type_name(obj), attr_name)
        new_link = self.od._create_link(link_name, slot_type, obj, new_target)
        self.recompute_mappings()

    def create_primitive_value(self, name: str, value: any, is_code=False):
        # watch out: in Python, 'bool' is subtype of 'int'
        #  so we must check for 'bool' first
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
        self.recompute_mappings()
        return tgt

    def overwrite_primitive_value(self, name: str, value: any, is_code=False):
        referred_model = UUID(self.bottom.read_value(self.get(name)))
        # watch out: in Python, 'bool' is subtype of 'int'
        #  so we must check for 'bool' first
        if isinstance(value, bool):
            Boolean(referred_model, self.state).create(value)
        elif isinstance(value, int):
            Integer(referred_model, self.state).create(value)
        elif isinstance(value, str):
            if is_code:
                ActionCode(referred_model, self.state).create(value)
            else:
                String(referred_model, self.state).create(value)
        else:
            raise Exception("Unimplemented type "+value)

    def create_link(self, link_name: Optional[str], assoc_name: str, src: UUID, tgt: UUID) -> UUID:
        global NEXT_ID
        types = self.bottom.read_outgoing_elements(self.mm, assoc_name) 
        if len(types) == 0:
            raise Exception(f"No such association: '{assoc_name}'")
        elif len(types) >= 2:
            raise Exception(f"More than one association exists with name '{assoc_name}' - this means the MM is invalid.")
        typ = types[0]
        if link_name == None:
            link_name = f"__{assoc_name}{NEXT_ID}"
            NEXT_ID += 1
        link_id = self.od._create_link(link_name, typ, src, tgt)
        self.recompute_mappings()
        return link_id

    def create_object(self, object_name: Optional[str], class_name: str) -> UUID:
        obj = self.od.create_object(object_name, class_name)
        self.recompute_mappings()
        return obj

# internal use
# Get API methods as bound functions, to pass as globals to 'eval'
# Readonly version is used for:
#  - Conformance checking
#  - Pattern matching (LHS/NAC of rule)
def bind_api_readonly(odapi):
    funcs = {
        'read_value': odapi.state.read_value,
        'get': odapi.get,
        'get_value': odapi.get_value,
        'get_target': odapi.get_target,
        'get_source': odapi.get_source,
        'get_slot': odapi.get_slot,
        'get_slots': odapi.get_slots,
        'get_slot_value': odapi.get_slot_value,
        'get_slot_value_default': odapi.get_slot_value_default,
        'get_all_instances': odapi.get_all_instances,
        'get_name': odapi.get_name,
        'get_type_name': odapi.get_type_name,
        'get_outgoing': odapi.get_outgoing,
        'get_incoming': odapi.get_incoming,
        'has_slot': odapi.has_slot,
        'is_instance': odapi.is_instance,
    }
    return funcs

# internal use
# Get API methods as bound functions, to pass as globals to 'eval'
# Read/write version is used for:
#  - Graph rewriting (RHS of rule)
def bind_api(odapi):
    funcs = {
        **bind_api_readonly(odapi),
        'create_object': odapi.create_object,
        'create_link': odapi.create_link,
        'delete': odapi.delete,
        'set_slot_value': odapi.set_slot_value
    }
    return funcs
