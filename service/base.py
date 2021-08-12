from abc import ABC, abstractmethod
from uuid import UUID


class Service(ABC):
    def __init__(self, model: UUID):
        self.model = model
