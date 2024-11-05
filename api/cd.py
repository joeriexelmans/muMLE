from services.bottom.V0 import Bottom
from uuid import UUID

class CDAPI:
    def __init__(self, state, m: UUID):
        self.state = state
        self.bottom = Bottom(state)
        self.m = m
        self.mm = UUID(state.read_value(state.read_dict(state.read_root(), "SCD")))

        # pre-compute some things

        # element -> name
        self.type_model_names = {
            self.bottom.read_outgoing_elements(self.m, e)[0]
                : e for e in self.bottom.read_keys(self.m)
        }


        inh_type, = self.bottom.read_outgoing_elements(self.mm, "Inheritance")
        inh_links = []
        for tm_element, tm_name in self.type_model_names.items():
            types = self.bottom.read_outgoing_elements(tm_element, "Morphism")
            if inh_type in types:
                inh_links.append(tm_element)

        # for each inheritance link we add the parent and child to the sub types map
        # name -> name
        self.direct_sub_types = { type_name: set() for type_name in self.bottom.read_keys(self.m) } # empty initially
        self.direct_super_types = { type_name: set() for type_name in self.bottom.read_keys(self.m) } # empty initially
        for link in inh_links:
            tm_source = self.bottom.read_edge_source(link)
            tm_target = self.bottom.read_edge_target(link)
            parent_name = self.type_model_names[tm_target]
            child_name = self.type_model_names[tm_source]
            self.direct_sub_types[parent_name].add(child_name)
            self.direct_super_types[child_name].add(parent_name)

        def get_transitive_sub_types(type_name: str):
            # includes the type itself - reason: if we want to get all the instances of some type and its subtypes, we don't have to consider the type itself as an extra case
            return [type_name, *(sub_type for child_name in self.direct_sub_types.get(type_name, set()) for sub_type in get_transitive_sub_types(child_name) )]

        def get_transitive_super_types(type_name: str):
            # includes the type itself - reason: if we want to check if something is an instance of a type, we check if its type or one of its super types is equal to the type we're looking for, without having to consider the instance's type itself as an extra case
            return [type_name, *(super_type for parent_name in self.direct_super_types.get(type_name, set()) for super_type in get_transitive_super_types(parent_name))]


        self.transitive_sub_types = { type_name: set(get_transitive_sub_types(type_name)) for type_name in self.direct_sub_types } 
        self.transitive_super_types = { type_name: set(get_transitive_super_types(type_name)) for type_name in self.direct_super_types }

    def get_type(self, type_name: str):
        return self.bottom.read_outgoing_elements(self.m, type_name)[0]

    def is_direct_subtype(self, super_type_name: str, sub_type_name: str):
        return sub_type_name in self.direct_sub_types[super_type]

    def is_direct_supertype(self, sub_type_name: str, super_type_name: str):
        return super_type_name in self.direct_super_types[sub_type_name]

    # Note: according to this function, every class is a subtype of itself
    def is_subtype(self, super_type_name: str, sub_type_name: str):
        return sub_type_name in self.transitive_sub_types[super_type_name]

    # Note: according to this function, every class is a supertype of itself
    def is_supertype(self, sub_type_name: str, super_type_name: str):
        return super_type_name in self.transitive_super_types[sub_type_name]

    # # The edge connecting an object to the value of a slot must be named `{object_name}_{attr_name}`
    def get_attr_link_name(self, class_name, attr_name):
        return self.type_model_names[self.find_attribute_type(class_name, attr_name)]

    # Attributes are inherited, so when we instantiate an attribute of a class, the AttributeLink may contain the name of the superclass
    def find_attribute_type(self, class_name: str, attr_name: str):
        assoc_name = f"{class_name}_{attr_name}"
        type_edges = self.bottom.read_outgoing_elements(self.m, assoc_name)
        if len(type_edges) == 1:
            return type_edges[0]
        else:
            for supertype in self.direct_super_types[class_name]:
                result = self.find_attribute_type(supertype, attr_name)
                if result != None:
                    return result
