import jinja2
import os
THIS_DIR = os.path.dirname(__file__)

from api.od import ODAPI
from examples.petrinet import helpers
from util.module_to_dict import module_to_dict

def export_tapaal(state, m, mm):
    loader = jinja2.FileSystemLoader(searchpath=THIS_DIR)
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template("tapaal.jinja2")
    return template.render({
        'odapi': ODAPI(state, m, mm),
        **globals()['__builtins__'],
        **module_to_dict(helpers),
    })
