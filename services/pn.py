from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from services.primitives.string_type import String

import re


class PN:
    def __init__(self, model: UUID, state: State):
        ltm_pn_id = state.read_dict(state.read_root(), "PN")
        self.ltm_pn = UUID(state.read_value(ltm_pn_id))
        self.model = model
        self.bottom = Bottom(state)

    def create_place(self, name: str, tokens: int):
        # instantiate Place class
        place_node = self.bottom.create_node()  # create place node
        self.bottom.create_edge(self.model, place_node, name)  # attach to model
        morph_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "P")  # retrieve type
        self.bottom.create_edge(place_node, morph_node, "Morphism")  # create morphism link
        # instantiate name attribute
        name_model = self.bottom.create_node()
        String(name_model, self.bottom.state).create(name)
        name_node = self.bottom.create_node(str(name_model))
        self.bottom.create_edge(self.model, name_node, f"{name}.n")
        name_link = self.bottom.create_edge(place_node, name_node)
        self.bottom.create_edge(self.model, name_link, f"{name}.n_link")
        ltm_pn_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "String")
        ltm_pn_link, = self.bottom.read_outgoing_elements(self.ltm_pn, "P_n")
        self.bottom.create_edge(name_node, ltm_pn_node, "Morphism")
        self.bottom.create_edge(name_link, ltm_pn_link, "Morphism")
        # instantiate tokens attribute
        tokens_model = self.bottom.create_node()
        Integer(tokens_model, self.bottom.state).create(tokens)
        tokens_node = self.bottom.create_node(str(tokens_model))
        self.bottom.create_edge(self.model, tokens_node, f"{name}.t")
        tokens_link = self.bottom.create_edge(place_node, tokens_node)
        self.bottom.create_edge(self.model, tokens_link, f"{name}.t_link")
        ltm_pn_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "Integer")
        ltm_pn_link, = self.bottom.read_outgoing_elements(self.ltm_pn, "P_t")
        self.bottom.create_edge(tokens_node, ltm_pn_node, "Morphism")
        self.bottom.create_edge(tokens_link, ltm_pn_link, "Morphism")

    def create_transition(self, name: str):
        # instantiate Transition class
        transition_node = self.bottom.create_node()  # create transition node
        self.bottom.create_edge(self.model, transition_node, name)  # attach to model
        morph_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "T")  # retrieve type
        self.bottom.create_edge(transition_node, morph_node, "Morphism")  # create morphism link
        # instantiate name attribute
        name_model = self.bottom.create_node()
        String(name_model, self.bottom.state).create(name)
        name_node = self.bottom.create_node(str(name_model))
        self.bottom.create_edge(self.model, name_node, f"{name}.name")
        name_link = self.bottom.create_edge(transition_node, name_node)
        self.bottom.create_edge(self.model, name_link, f"{name}.name_link")
        ltm_pn_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "String")
        ltm_pn_link, = self.bottom.read_outgoing_elements(self.ltm_pn, "T_name")
        self.bottom.create_edge(name_node, ltm_pn_node, "Morphism")
        self.bottom.create_edge(name_link, ltm_pn_link, "Morphism")

    def create_p2t(self, place: str, transition: str, weight: int):
        # create p2t link + morphism links
        edge = self.bottom.create_edge(
            *self.bottom.read_outgoing_elements(self.model, place),
            *self.bottom.read_outgoing_elements(self.model, transition),
        )
        self.bottom.create_edge(self.model, edge, f"{place}_to_{transition}")  # attach to model
        morph_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "P2T")  # retrieve type
        self.bottom.create_edge(edge, morph_node, "Morphism")  # create morphism link
        # weight attribute
        weight_model = self.bottom.create_node()
        Integer(weight_model, self.bottom.state).create(weight)
        weight_node = self.bottom.create_node(str(weight_model))
        self.bottom.create_edge(self.model, weight_node, f"{place}_to_{transition}.weight")
        weight_link = self.bottom.create_edge(edge, weight_node)
        self.bottom.create_edge(self.model, weight_link, f"{place}_to_{transition}.weight_link")
        scd_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "Integer")
        scd_link, = self.bottom.read_outgoing_elements(self.ltm_pn, "P2T_weight")
        self.bottom.create_edge(weight_node, scd_node, "Morphism")
        self.bottom.create_edge(weight_link, scd_link, "Morphism")

    def create_t2p(self, transition: str, place: str, weight: int):
        # create t2p link + morphism links
        edge = self.bottom.create_edge(
            *self.bottom.read_outgoing_elements(self.model, transition),
            *self.bottom.read_outgoing_elements(self.model, place),
        )
        self.bottom.create_edge(self.model, edge, f"{transition}_to_{place}")  # attach to model
        morph_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "T2P")  # retrieve type
        self.bottom.create_edge(edge, morph_node, "Morphism")  # create morphism link
        # weight attribute
        weight_model = self.bottom.create_node()
        Integer(weight_model, self.bottom.state).create(weight)
        weight_node = self.bottom.create_node(str(weight_model))
        self.bottom.create_edge(self.model, weight_node, f"{transition}_to_{place}.weight")
        weight_link = self.bottom.create_edge(edge, weight_node)
        self.bottom.create_edge(self.model, weight_link, f"{transition}_to_{place}.weight_link")
        scd_node, = self.bottom.read_outgoing_elements(self.ltm_pn, "Integer")
        scd_link, = self.bottom.read_outgoing_elements(self.ltm_pn, "T2P_weight")
        self.bottom.create_edge(weight_node, scd_node, "Morphism")
        self.bottom.create_edge(weight_link, scd_link, "Morphism")

    def list_elements(self):
        pn_names = {}
        for key in self.bottom.read_keys(self.ltm_pn):
            element, = self.bottom.read_outgoing_elements(self.ltm_pn, key)
            pn_names[element] = key
        unsorted = []
        for key in self.bottom.read_keys(self.model):
            element, = self.bottom.read_outgoing_elements(self.model, key)
            element_types = self.bottom.read_outgoing_elements(element, "Morphism")
            type_model_elements = self.bottom.read_outgoing_elements(self.ltm_pn)
            element_type_node, = [e for e in element_types if e in type_model_elements]
            unsorted.append((key, pn_names[element_type_node]))
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
