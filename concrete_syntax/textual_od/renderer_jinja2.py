import jinja2
import os
from uuid import UUID

THIS_DIR = os.path.dirname(__file__)

from api.od import ODAPI
from concrete_syntax import common
from services.bottom.V0 import Bottom
from util.module_to_dict import module_to_dict

def render_od_jinja2(state, m, mm):
    bottom = Bottom(state)
    type_model_id = state.read_dict(state.read_root(), "SCD")
    scd_model = UUID(state.read_value(type_model_id))
    type_odapi = ODAPI(state, mm, scd_model)

    objects = []
    links = []

    to_add = bottom.read_keys(m)
    already_added = set()

    while len(to_add) > 0:
        next_round = []
        for obj_name in to_add:
            obj = state.read_dict(m, obj_name)
            src, tgt = state.read_edge(obj)
            if src == None:
                # not a link
                objects.append((obj_name, obj))
                already_added.add(obj)
            else:
                # A link can only be written out after its source and target have been written out
                if src in already_added and tgt in already_added:
                    links.append((obj_name, obj))
                else:
                    # try again later
                    next_round.append(obj_name)
        if len(next_round) == len(to_add):
            raise Exception("We got stuck!", next_round)
        to_add = next_round

    loader = jinja2.FileSystemLoader(searchpath=THIS_DIR)
    environment = jinja2.Environment(
        loader=loader,
        # whitespace control:
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("objectdiagrams.jinja2")
    return template.render({
        'objects': objects,
        'links': links,
        'odapi': ODAPI(state, m, mm),
        **globals()['__builtins__'],
        **module_to_dict(common),
    })
