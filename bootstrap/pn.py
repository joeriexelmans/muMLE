from services.scd import SCD
from uuid import UUID
from state.base import State


def bootstrap_pn(state: State, model_name: str) -> UUID:
    # Retrieve scd model
    scd_id = state.read_dict(state.read_root(), "SCD")
    scd = UUID(state.read_value(scd_id))
    # Retrieve refs to primitive type models
    # # integer
    int_type_id = state.read_dict(state.read_root(), "Integer")
    int_type = UUID(state.read_value(int_type_id))
    # # string
    str_type_id = state.read_dict(state.read_root(), "String")
    str_type = UUID(state.read_value(str_type_id))
    # Create LTM_PN
    model_uuid = state.create_node()
    mcl_root_id = state.create_nodevalue(str(model_uuid))
    state.create_dict(state.read_root(), model_name, mcl_root_id)
    service = SCD(scd, model_uuid, state)
    # Create classes
    service.create_class("P")
    service.create_class("T")
    # Create associations
    service.create_association("P2T", "P", "T")
    service.create_association("T2P", "T", "P")
    # Create model refs
    service.create_model_ref("Integer", int_type)
    service.create_model_ref("String", str_type)
    # Create class attributes
    service.create_attribute_link("P", "Integer", "t", False)
    service.create_attribute_link("P", "String", "n", False)
    service.create_attribute_link("T", "String", "n", False)
    # Create association attributes
    service.create_attribute_link("P2T", "Integer", "w", False)
    service.create_attribute_link("T2P", "Integer", "w", False)
    # Create test constraint
    service.add_constraint("P", "print(element)\nreturn True")
    return model_uuid
