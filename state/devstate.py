from state.pystate import PyState
from uuid import UUID


class DevState(PyState):
    """
    Version of PyState that allows dumping to .dot files
    + node id's are generated sequentially to make writing tests easier
    """

    def __init__(self):
        self.free_id = 0
        super().__init__()

    def new_id(self) -> UUID:
        self.free_id += 1
        return UUID(int=self.free_id - 1)

    def dump(self, path: str, png_path: str = None):
        """Dumps the whole MV graph to a graphviz .dot-file

        Args:
            path (str): path for .dot-file
            png_path (str, optional): path for .png image generated from the .dot-file. Defaults to None.
        """
        with open(path, "w") as f:
            f.write("digraph main {\n")
            for n in sorted(self.nodes):
                if n in self.values:
                    x = self.values[n]
                    if isinstance(x, tuple):
                        x = f"{x[0]}"
                    else:
                        x = repr(x)
                    f.write("\"a_%s\" [label=\"%s\"];\n" % (
                        n.int, x.replace('"', '\\"')))
                else:
                    f.write("\"a_%s\" [label=\"\"];\n" % n)
            for i, e in sorted(list(self.edges.items())):
                f.write("\"a_%s\" [label=\"e_%s\" shape=point];\n" % (i.int, i.int))
                f.write("\"a_%s\" -> \"a_%s\" [arrowhead=none];\n" % (e[0].int, i.int))
                f.write("\"a_%s\" -> \"a_%s\";\n" % (i.int, e[1].int))
            f.write("}")

        if png_path is not None:
            # generate png from dot-file
            bashCommand = f"dot -Tpng {path} -o {png_path}"
            import subprocess
            process = subprocess.Popen(
                bashCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
