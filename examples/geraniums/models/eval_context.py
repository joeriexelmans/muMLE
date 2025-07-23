import os

from jinja2 import Environment, FileSystemLoader

from api.od import ODAPI
from framework.conformance import eval_context_decorator


@eval_context_decorator
def _render_geraniums_dot(od: ODAPI, file: str) -> str:
    __DIR__ = os.path.dirname(__file__)
    env = Environment(
        loader=FileSystemLoader(
            __DIR__
        )
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    template_dot = env.get_template("geraniums_renderer.j2")

    id_count = 0
    id_map = {}
    render = {"geraniums": [], "pots": [], "planted": []}

    for name, uuid in od.get_all_instances("Geranium"):
        render["geraniums"].append((id_count, name, od.get_slot_value(uuid, "flowering")))
        id_map[uuid] = id_count
        id_count += 1

    for name, uuid in od.get_all_instances("Pot"):
        render["pots"].append((id_count, name, od.get_slot_value(uuid, "cracked")))
        id_map[uuid] = id_count
        id_count += 1

    for name, uuid in od.get_all_instances("Planted"):
        render["planted"].append((id_map[od.get_source(uuid)], id_map[od.get_target(uuid)]))

    with open(file, "w", encoding="utf-8") as f_dot:
        f_dot.write(template_dot.render(**render))
    return ""

eval_context = {
    "render_geraniums_dot": _render_geraniums_dot,
}
