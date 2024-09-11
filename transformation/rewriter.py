# Things you can do:
#   - Create/delete objects, associations, attributes
#   - Change attribute values
#   - ? that's it?

from uuid import UUID
from services.bottom.V0 import Bottom

def process_rule(state, lhs: UUID, rhs: UUID):
    bottom = Bottom(state)

    # : bottom.read_outgoing_elements(rhs, name)[0]
    to_delete = { name for name in bottom.read_keys(lhs) if name not in bottom.read_keys(rhs) }
    to_create = { name for name in bottom.read_keys(rhs) if name not in bottom.read_keys(lhs) }

    print("to_delete:", to_delete)
    print("to_create:", to_create)

    return to_delete, to_create

def rewrite(state, lhs: UUID, rhs: UUID, match_mapping: dict, model_to_transform: UUID) -> UUID:
    bottom = Bottom(state)

    to_delete, to_create = process_rule(state, lhs, rhs)

    for pattern_name_to_delete in to_delete:
        # For every name in `to_delete`, look up the name of the matched element in the host graph
        model_element_name_to_delete = match_mapping[pattern_name_to_delete]
        print('deleting', model_element_name_to_delete)
        # Look up the matched element in the host graph
        element_to_delete, = bottom.read_outgoing_elements(model_to_transform, model_element_name_to_delete)
        # Delete
        bottom.delete_element(element_to_delete)

    for pattern_name_to_create in to_create:
        pass