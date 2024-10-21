from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_cd import parser as parser_cd
from concrete_syntax.textual_od import parser as parser_od
from concrete_syntax.textual_od import renderer as renderer_od
from concrete_syntax.common import indent
from concrete_syntax.plantuml import renderer as plantuml
from util.prompt import yes_no, pause

state = DevState()

print("Loading meta-meta-model...")
scd_mmm = bootstrap_scd(state)
print("OK")

print("Is our meta-meta-model a valid class diagram?")
conf = Conformance(state, scd_mmm, scd_mmm)
print(render_conformance_check_result(conf.check_nominal()))

# If you are curious, you can serialize the meta-meta-model:
# print("--------------")
# print(indent(
#     renderer.render_od(state,
#         m_id=scd_mmm,
#         mm_id=scd_mmm),
#     4))
# print("--------------")


# Change this:
woods_mm_cs = """
    abstract class Animal

    class Bear (Animal) # Bear inherits Animal

    class Man [1..2] (Animal) {
        Integer weight `get_value(get_target(this)) > 20`; # <- constraint in context of attribute-link

        `get_value(get_slot(this, "weight")) > 20` # <- constraint in context of Man-object
    }

    association afraidOf  [0..6] Man -> Animal [1..2]

    global total_weight_small_enough ```
        total_weight = 0
        for man_name, man_id in get_all_instances("Man"):
            total_weight += get_value(get_slot(man_id, "weight"))
        total_weight < 85
    ```
"""

print()
print("Parsing 'woods' meta-model...")
woods_mm = parser_cd.parse_cd(
    state,
    m_text=woods_mm_cs, # the string of text to parse
)
print("OK")

# We can serialize the class diagram to our object diagram syntax
#  (because the class diagram IS also an object diagram):
print("--------------")
print(indent(
    renderer_od.render_od(state,
        m_id=woods_mm,
        mm_id=scd_mmm),
    4))
print("--------------")

print("Is our 'woods' meta-model a valid class diagram?")
conf = Conformance(state, woods_mm, scd_mmm)
print(render_conformance_check_result(conf.check_nominal()))

# Change this:
woods_m_cs = """
    george:Man {
        weight = 15;
    }
    billy:Man {
        weight = 100;
    }
    bear1:Bear
    bear2:Bear
    :afraidOf (george -> bear1)
    :afraidOf (george -> bear2)
"""

print()
print("Parsing 'woods' model...")
woods_m = parser_od.parse_od(
    state,
    m_text=woods_m_cs,
    mm=woods_mm, # this time, the meta-model is the previous model we parsed
)
print("OK")

# As a double-check, you can serialize the parsed model:
# print("--------------")
# print(indent(
#     renderer.render_od(state,
#         m_id=woods_m,
#         mm_id=woods_mm),
#     4))
# print("--------------")

print("Is our model a valid woods-diagram?")
conf = Conformance(state, woods_m, woods_mm)
print(render_conformance_check_result(conf.check_nominal()))


print()
print("==================================")
if yes_no("Print PlantUML?"):
    print_mm = yes_no("  ▸ Print meta-model?")
    print_m = yes_no("  ▸ Print model?")
    print_conf = print_mm and print_m and yes_no("  ▸ Print conformance links?")

    uml = ""
    if print_mm:
        uml += plantuml.render_package("Meta-model", plantuml.render_class_diagram(state, woods_mm))
    if print_m:
        uml += plantuml.render_package("Model", plantuml.render_object_diagram(state, woods_m, woods_mm))
    if print_conf:
        uml += plantuml.render_trace_conformance(state, woods_m, woods_mm)

    print("==================================")
    print(uml)
    print("==================================")
    print("Go to either:")
    print("  ▸ https://www.plantuml.com/plantuml/uml")
    print("  ▸ https://mstro.duckdns.org/plantuml/uml")
    print("and paste the above string.")
