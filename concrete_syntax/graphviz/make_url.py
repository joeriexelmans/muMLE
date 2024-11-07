from concrete_syntax.common import indent
import urllib.parse

def make_url(graphviz_txt: str) -> str:

    as_digraph = f"digraph {{\n{indent(graphviz_txt, 2)}\n}}"

    # This one seems much faster:
    return "https://edotor.net/?engine=dot#"+urllib.parse.quote(as_digraph)

    # Keeping this one here just in case:
    # return "https://dreampuf.github.io/GraphvizOnline/#"+urllib.parse.quote(graphviz)
