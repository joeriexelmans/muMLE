from .singleton import Singleton

class IdGenerator(metaclass=Singleton):
    def __init__(self):
        self.id = -1
    def generate_id(self) -> int:
        self.id += 1
        return self.id