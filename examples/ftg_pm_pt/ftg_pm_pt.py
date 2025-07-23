import os

# Todo: remove src.backend.muMLE from the imports
from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od.parser import parse_od
from api.od import ODAPI
from concrete_syntax.textual_od.renderer import render_od as od_renderer
from concrete_syntax.plantuml import make_url as plant_url, renderer as plant_renderer
from concrete_syntax.graphviz import make_url as graphviz_url, renderer as graphviz_renderer

class FtgPmPt:

    def __init__(self, name: str):
        self.state = DevState()
        self.scd_mmm = bootstrap_scd(self.state)
        self.meta_model = self.load_metamodel()
        self.model = None
        self.odapi = None
        self.name = name

    @staticmethod
    def read_file(file_name):
        with open(os.path.join(os.path.dirname(__file__), file_name)) as file:
            return file.read()

    def load_metamodel(self):
        mm_cs = self.read_file("pm/metamodels/mm_design.od")
        mm_rt_cs = mm_cs + self.read_file("pm/metamodels/mm_runtime.od")
        mm_total = mm_rt_cs + self.read_file("pt/metamodels/mm_design.od")
        return parse_od(self.state, m_text=mm_total, mm=self.scd_mmm)

    def load_model(self, m_text: str | None = None):
        m_text = "" if not m_text else m_text
        self.model = parse_od(self.state, m_text=m_text, mm=self.meta_model)
        self.odapi = ODAPI(self.state, self.model, self.meta_model)

    def render_od(self):
        return od_renderer(self.state, self.model, self.meta_model, hide_names=False)

    def render_plantuml_object_diagram(self):
        print(plant_url.make_url(plant_renderer.render_package(
            self.name, plant_renderer.render_object_diagram(self.state, self.model, self.meta_model)))
        )

    def render_graphviz_object_diagram(self):
        print(graphviz_url.make_url(graphviz_renderer.render_object_diagram(self.state, self.model, self.meta_model)))