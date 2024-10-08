from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser, renderer
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
    Animal:Class {
        # The class Animal is an abstract class:
        abstract = True;
    }

    # A class without attributes
    # The `abstract` attribute shown above is optional (default: False)
    Bear:Class

    # Inheritance between two Classes is expressed as follows:
    :Inheritance (Bear -> Animal)  # meaning: Bear is an Animal

    Man:Class {
        # We can define lower and upper cardinalities on Classes
        # (if unspecified, the lower-card is 0, and upper-card is infinity)
        lower_cardinality = 1; # there must be at least one Man in every model
        upper_cardinality = 2; # there must be at most two Men in every model

        constraint = ```
            # Python code
            # the last statement must be a boolean expression

            # When conformance checking, this code will be run for every Man-object.
            # The variable 'this' refers to the current Man-object.

            # Every man weighs at least '20'
            # (the attribute 'weight' is added further down)
            get_value(get_slot(this, "weight")) > 20
        ```;
    }
    # Note that we can only declare the inheritance link after having declared both Man and Animal: We can only refer to earlier objects
    :Inheritance (Man -> Animal) # Man is also an Animal


    # BTW, we could also give the Inheritance-link a name, for instance:
    #    man_is_animal:Inheritance (Man -> Animal)
    #
    # Likewise, Classes, Associations, ... can also be nameless, for instance:
    #    :Class { ... }
    #    :Association (Man -> Man) { ... }
    # However, we typically want to give names to classes and associations, because we want to refer to them later.


    # We now add an attribute to 'Man'
    # Attributes are not that different from Associations: both are represented by links
    Man_weight:AttributeLink (Man -> Integer) {
        name = "weight"; # mandatory!
        optional = False; # <- meaning: every Man *must* have a weight

        # We can also define constraints on attributes
        constraint = ```
            # Python code
            # Here, 'this' refers to the LINK that connects a Man-object to an Integer
            tgt = get_target(this) # <- we get the target of the LINK (an Integer-object)
            weight = get_value(tgt) # <- get the Integer-value (e.g., 80)
            weight > 20
        ```;
    }

    # Create an Association from Man to Animal
    afraidOf:Association (Man -> Animal) {
        # An association has the following (optional) attributes:
        #    - source_lower_cardinality (default: 0)
        #    - source_upper_cardinality (default: infinity)
        #    - target_lower_cardinality (default: 0)
        #    - target_upper_cardinality (default: infinity)

        # Every Man is afraid of at least one Animal:
        target_lower_cardinality = 1;

        # No more than 6 Men are afraid of the same Animal:
        source_upper_cardinality = 6;
    }

    # Create a GlobalConstraint
    total_weight_small_enough:GlobalConstraint {
        # Note: for GlobalConstraints, there is no 'this'-variable
        constraint = ```
            # Python code
            # compute sum of all weights
            total_weight = 0
            for man_name, man_id in get_all_instances("Man"):
                total_weight += get_value(get_slot(man_id, "weight"))

            # as usual, the last statement is a boolean expression that we think should be satisfied
            total_weight < 85
        ```;
    }
"""

print()
print("Parsing 'woods' meta-model...")
woods_mm = parser.parse_od(
    state,
    m_text=woods_mm_cs, # the string of text to parse
    mm=scd_mmm, # the meta-model of class diagrams (= our meta-meta-model)
)
print("OK")

# As a double-check, you can serialize the parsed model:
# print("--------------")
# print(indent(
#     renderer.render_od(state,
#         m_id=woods_mm,
#         mm_id=scd_mmm),
#     4))
# print("--------------")

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
woods_m = parser.parse_od(
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
    print("Go to http://www.plantuml.com/plantuml/uml/")
    print("and paste the above string.")
