# Before we can create a model in muMLE, we have to create a meta-model.

# Here's an example of a (silly) meta-model.
# We use a textual concrete syntax:

mm_cs = """
    # A class named 'A':
    A:Class

    # A class named 'B':
    B:Class

    # An association from 'A' to 'B':
    a2b:Association (A -> B) {
        # Every 'A' must be associated with at least one 'B'
        target_lower_cardinality = 1;
    }
"""

# Now, we create a model that is an instance of our meta-model:

m_cs = """
    myA:A

    myB:B

    myLnk:a2b (myA -> myB)
"""

# Notice that the syntax for meta-model and model is the same: We always declare a named object/link, followed by a colon (:) and the name of the type. The type name refers to the name of an object/link in the meta-model of our model.


# So far we've only created text strings in Python. To parse them as models, we first create our 'state', which is a mutable graph that will contain our models and meta-models:


from state.devstate import DevState

state = DevState()


# Next, we must load the Simple Class Diagrams (SCD) meta-meta-model into our 'state'. The SCD meta-meta-model is a meta-model for our meta-model, and it is also a meta-model for itself.

# The meta-meta-model is not specified in textual syntax because it is typed by itself. In textual syntax, it would contain things like:
#    Class:Class
# which is an object typed by itself. The parser cannot handle this (or circular dependencies in general). Therefore, we load the meta-meta-model by mutating the 'state' directly at a very low level:

from bootstrap.scd import bootstrap_scd

print("Loading meta-meta-model...")
mmm = bootstrap_scd(state)
print("OK")

# Now that the meta-meta-model has been loaded, we can parse our meta-model:

from concrete_syntax.textual_od import parser

print()
print("Parsing meta-model...")
mm = parser.parse_od(
    state,
    m_text=mm_cs, # the string of text to parse
    mm=mmm, # the meta-model of class diagrams (= our meta-meta-model)
)
print("OK")


# And we can parse our model, the same way:

print()
print("Parsing model...")
m = parser.parse_od(
    state,
    m_text=m_cs,
    mm=mm, # this time, the meta-model is the previous model we parsed
)
print("OK")


# Now we can do a conformance check:

from framework.conformance import Conformance, render_conformance_check_result

print()
print("Is our model a valid instance of our meta model?")
conf = Conformance(state, m, mm)
print(render_conformance_check_result(conf.check_nominal()))

# Looks like it is OK!


# We can also check if our meta-model is a valid class diagram:

print()
print("Is our meta-model a valid class diagram?")
conf = Conformance(state, mm, mmm)
print(render_conformance_check_result(conf.check_nominal()))

# Also good.


# Finally, we can even check if the meta-meta-model is a valid instance of itself (it should be):

print()
print("Is our meta-model a valid class diagram?")
conf = Conformance(state, mmm, mmm)
print(render_conformance_check_result(conf.check_nominal()))

# All good!


# Now let's make things a bit more interesting and introduce non-conformance:

m2_cs = """
    myA:A
    myA2:A

    myB:B

    myLnk:a2b (myA -> myB)
"""

# Parse it:

m2 = parser.parse_od(
    state,
    m_text=m2_cs,
    mm=mm,
)

# The above model is non-conformant because 'myA2' should have at least one outgoing link of type 'a2b', but it doesn't.

print()
print("Is model 'm2' a valid instance of our meta-model? (it should not be)")
conf = Conformance(state, m2, mm)
print(render_conformance_check_result(conf.check_nominal()))

# It should be non-conformant.


# Finally, let's render everything as PlantUML:

from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url

uml = (""
 + plantuml.render_package("Meta-model", plantuml.render_class_diagram(state, mm))
 + plantuml.render_package("Model", plantuml.render_object_diagram(state, m, mm))
 + plantuml.render_trace_conformance(state, m, mm)
 # + plantuml.render_package("Meta-meta-model", plantuml.render_class_diagram(state, mmm))
 # + plantuml.render_trace_conformance(state, mm, mmm)
)

print()
print("PlantUML output:", make_url(uml))


# On to the next tutorial...
