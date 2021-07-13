from state.pystate import PyState


class DevState(PyState):
    """
    Version of PyState that allows dumping to .dot files
    + node id's are generated sequentially to make writing tests easier
    """

    free_id = 0

    def __init__(self):
        super().__init__()

    @staticmethod
    def new_id() -> str:
        DevState.free_id += 1
        return str(DevState.free_id - 1)

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
                    if isinstance(x, dict):
                        x = f"{x.get('type')}"
                    else:
                        x = repr(x)
                    f.write("\"a_%s\" [label=\"%s\"];\n" % (
                        n, x.replace('"', '\\"')))
                else:
                    f.write("\"a_%s\" [label=\"\"];\n" % n)
            for i, e in sorted(list(self.edges.items())):
                f.write("\"a_%s\" [label=\"e_%s\" shape=point];\n" % (i, i))
                f.write("\"a_%s\" -> \"a_%s\" [arrowhead=none];\n" % (e[0], i))
                f.write("\"a_%s\" -> \"a_%s\";\n" % (i, e[1]))
            f.write("}")

        if png_path is not None:
            # generate png from dot-file
            bashCommand = f"dot -Tpng {path} -o {png_path}"
            import subprocess
            process = subprocess.Popen(
                bashCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
