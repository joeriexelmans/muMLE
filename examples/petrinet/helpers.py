from uuid import UUID

def get_num_tokens(odapi, place: UUID):
    pn_of = odapi.get_incoming(place, "pn_of")[0]
    place_state = odapi.get_source(pn_of)
    return odapi.get_slot_value(place_state, "numTokens")
