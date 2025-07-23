# We now get to the interesting part: model transformation.

# We start with a meta-model and a model, and parse them:

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from util import loader
from concrete_syntax.textual_od.renderer import render_od
from concrete_syntax.common import indent
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.plantuml.make_url import make_url as make_plantuml_url
from framework.conformance import Conformance, render_conformance_check_result

mm_cs = """
    Bear:Class
    Animal:Class {
        abstract = True;
    }
    Man:Class {
        lower_cardinality = 1;
        upper_cardinality = 2;
    }
    Man_weight:AttributeLink (Man -> Integer) {
        name = "weight";
        optional = False;
    }
    afraidOf:Association (Man -> Animal) {
        # Every Man afraid of at least one Animal
        target_lower_cardinality = 1;
    }
    :Inheritance (Man -> Animal)
    :Inheritance (Bear -> Animal)
"""

m_cs = """
    george:Man {
        weight = 80;
    }
    mrBrown:Bear
    teddy:Bear
    :afraidOf (george -> mrBrown)
    :afraidOf (george -> teddy)
"""

state = DevState()
mmm = bootstrap_scd(state)
mm = loader.parse_and_check(state, mm_cs, mmm, "mm")
m = loader.parse_and_check(state, m_cs, mm, "m")


# We will perform a simple model transformation, where we specify a Left Hand Side (LHS) and Right Hand Side (RHS) pattern. As we will see, both the LHS- and RHS-patterns are models too, and thus we need a meta-model for them. This meta-model can be auto-generated as follows:

from transformation.ramify import ramify

ramified_mm = ramify(state, mm)

# Let's see what it looks like:

print("RAMified meta-model:")
print(indent(render_od(state, ramified_mm, mmm), 2))

# Note that our RAMified meta-model is also a valid class diagram:

print()
print("Is valid class diagram?")
print(render_conformance_check_result(Conformance(state, ramified_mm, mmm).check_nominal()))

# We now specify our patterns.
# We create a rule that looks for a Man with weight > 60, who is afraid of an animal:

lhs_cs = """
    # object to match
    man:RAM_Man {
        # match only men heavy enough
        RAM_weight = `get_value(this) > 60`;
    }

    scaryAnimal:RAM_Animal
    manAfraidOfAnimal:RAM_afraidOf (man -> scaryAnimal)
"""

lhs = loader.parse_and_check(state, lhs_cs, ramified_mm, "lhs")

# As you can see, in our pattern-language, the names of the types have been prefixed with 'RAM_'. This is to distinguish them from the original types.
# Further, the type of the 'weight'-attribute has changed: it used to be Integer, but now it's ActionCode, meaning we can write Python-expression in it. In a LHS-pattern, we write an expression that evaluates to a (Python) boolean. In our example, the expression is evaluated on every Man-object. If the result is True, the object can be matched, otherwise it cannot.


# Let's see what happens if we match our LHS-pattern with our model:

from transformation.matcher import match_od

generator = match_od(state, m, mm, lhs, ramified_mm)

# Matching is lazy: 'match_od' returns a generator object, so it will only look for the next match if you ask it to do so. The reason is that sometimes, we're only interested in the first match, whereas producing all the matches can take a lot of time on big models, and the number of matches can also be very big. But our example is small so let's just generate all the matches:

all_matches = list(generator) # generate all matches

import pprint

print()
print("All matches:\n", pprint.pformat(all_matches))

# A match is just a Python dictionary mapping names of our LHS-pattern to names of our model.
# There should be 2 matches: 'man' will always be matched with 'george', but 'scaryAnimal' can be matched with either 'mrBrown' or 'teddy'.


# So far we've only queried our model. We can modify the model by specifying a RHS-pattern:
#   Objects/links that occur in RHS but not in LHS are CREATED
#   Objects/links that occur in LHS but not in RHS are DELETED
#   Objects/links that occur in both LHS and RHS remain, but we can still UPDATE their attributes.

# Here's a RHS-pattern:

rhs_cs = """
    man:RAM_Man {
        # man gains weight
        RAM_weight = `get_value(this) + 5`;
    }

    # to create:
    bill:RAM_Man {
        RAM_weight = `100`;
    }
    billAfraidOfMan:RAM_afraidOf (bill -> man)
"""

rhs = loader.parse_and_check(state, rhs_cs, ramified_mm, "rhs")


# Our RHS-pattern does not contain the objects 'scaryAnimal' or 'manAfraidOfAnimal' of our LHS, so these will be deleted. The objects 'bill' and 'billAfraidOfMan' will be created. The attribute 'weight' of 'man' (matched with 'george' in our example) will be incremented by 5.

# Notice that the weight of the new object 'bill' is the Python-expression `100` (in backticks), not the Integer 100.

# Let's rewrite our model:

from transformation.cloner import clone_od
from transformation import rewriter

m_rewritten = clone_od(state, m, mm) # copy our model before rewriting (this is optional - we do this so we can later render the model before and after rewrite in a single PlantUML diagram)

lhs_match = all_matches[0] # select one match
rhs_match = rewriter.rewrite(state, lhs, rhs, ramified_mm, lhs_match, m_rewritten, mm)

# Let's render everything as PlantUML:

uml = (""
    + plantuml.render_package("MM", plantuml.render_class_diagram(state, mm))
    + plantuml.render_package("RAMified MM", plantuml.render_class_diagram(state, ramified_mm))
    + plantuml.render_package("LHS", plantuml.render_object_diagram(state, lhs, ramified_mm))
    + plantuml.render_package("RHS", plantuml.render_object_diagram(state, rhs, ramified_mm))
    + plantuml.render_package("M (before rewrite)", plantuml.render_object_diagram(state, m, mm))
    + plantuml.render_package("M (after rewrite)", plantuml.render_object_diagram(state, m_rewritten, mm))

    + plantuml.render_trace_ramifies(state, mm, ramified_mm)

    + plantuml.render_trace_match(state, lhs_match, lhs, m, "orange")
    + plantuml.render_trace_match(state, rhs_match, rhs, m_rewritten, "red")

    + plantuml.render_trace_conformance(state, lhs, ramified_mm)
    + plantuml.render_trace_conformance(state, rhs, ramified_mm)
    + plantuml.render_trace_conformance(state, m, mm)
    + plantuml.render_trace_conformance(state, m_rewritten, mm)
)

print()
print("PlantUML:", make_plantuml_url(uml))

