from typing import Callable

def generate_dot_wrap(func) -> Callable:
    def wrapper(self, *args, **kwargs) -> str:
        nodes = []
        edges = []
        self.reset_visited()
        func(self, nodes, edges, *args, **kwargs)
        return f"digraph G {{\n\t{"\n\t".join(nodes)}\n\t{"\n\t".join(edges)}\n}}"
    return wrapper
