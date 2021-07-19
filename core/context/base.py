from abc import ABC, abstractmethod
from state.base import State
from core.element import Element, String


class Context(ABC):
    def __init__(self, state: State, model: Element, metamodel: Element):
        self.state = state
        self.model = model
        self.metamodel = metamodel

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self):
        pass

    @abstractmethod
    def exposed_methods(self):
        pass

    @abstractmethod
    def instantiate(self, type_name: String, instance_name: String):
        pass

    @abstractmethod
    def instantiate_value(self, type_name: String, instance_name: String, value: Element):
        pass

    @abstractmethod
    def instantiate_link(self, type_name: String, name: String, source: String, target: String):
        pass

    @abstractmethod
    def delete_element(self, name: String):
        pass

    @abstractmethod
    def verify(self):
        pass

    @abstractmethod
    def list_elements(self):
        pass

    def list_types(self):
        # can be implemented here since we assume that metamodel
        # is always in graph fo, i.e. in the MV-state graph.
        unsorted = []
        model_root = self.state.read_dict(self.metamodel.id, "Model")
        for elem_edge in self.state.read_outgoing(model_root):
            # get element name
            label_edge, = self.state.read_outgoing(elem_edge)
            _, label_node = self.state.read_edge(label_edge)
            label = self.state.read_value(label_node)
            # find element type
            elem_type_node = self.state.read_dict(label_node, "Type")
            elem_type = self.state.read_value(elem_type_node)
            unsorted.append(f"{label} : {elem_type if elem_type is not None else '_'}")
        for i in sorted(unsorted):
            print(i)
