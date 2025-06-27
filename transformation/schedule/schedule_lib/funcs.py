from typing import Callable, List

from jinja2 import Template

from .singleton import Singleton


class IdGenerator(metaclass=Singleton):
    exec_id = -1
    node_id = -1

    @classmethod
    def generate_node_id(cls) -> int:
        cls.node_id +=1
        return cls.node_id

    @classmethod
    def generate_exec_id(cls) -> int:
        cls.exec_id += 1
        return cls.exec_id

def generate_dot_wrap(func) -> Callable:
    def wrapper(self, *args, **kwargs) -> str:
        nodes = []
        edges = []
        self.reset_visited()
        func(self, nodes, edges, *args, **kwargs)
        return f"digraph G {{\n\t{"\n\t".join(nodes)}\n\t{"\n\t".join(edges)}\n}}"

    return wrapper


def not_visited(func) -> Callable:
    def wrapper(
        self, nodes: List[str], edges: List[str], visited: set[int], *args, **kwargs
    ) -> None:
        if self in visited:
            return
        visited.add(self)
        func(self, nodes, edges, visited, *args, **kwargs)

    return wrapper


def generate_dot_node(self, nodes: List[str], template: Template, **kwargs) -> None:
    nodes.append(template.module.__getattribute__("Node")(**{**kwargs, "id": self.id}))


def generate_dot_edge(
    self, target, edges: List[str], template: Template, kwargs
) -> None:
    edges.append(
        template.module.__getattribute__("Edge")(
            **{**kwargs, "from_id": self.id, "to_id": target.id}
        )
    )
