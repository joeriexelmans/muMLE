from state.base import State
from uuid import UUID
from services.bottom.V0 import Bottom
from services.scd import SCD

def ramify(state: State, model: UUID) -> UUID:
    """
    Parameters:
        bottom: Bottom-service, wrapping MVS
        model: An SCD-conforming meta-model to ramify
    """
    scd = SCD(model, state)

    classes = scd.get_classes()
    print(classes)

    attrs = scd.get_attributes('A')
    print(attrs)
