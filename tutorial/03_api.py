# We reuse our (meta-)model from the previous tutorial. For this tutorial, it doesn't really matter what the models look like.

mm_cs = """
    MyAbstractClass:Class {
        abstract = True;
    }

    MyConcreteClass:Class

    :Inheritance (MyConcreteClass -> MyAbstractClass)

    Z:Class

    myZ:Association (MyAbstractClass -> Z) {
        target_lower_cardinality = 1;
    }
"""

m_cs = """
    cc:MyConcreteClass
    z:Z
    :myZ (cc -> z)
"""


# We parse everything:

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from util import loader

state = DevState()
mmm = bootstrap_scd(state)
mm = loader.parse_and_check(state, mm_cs, mmm, "mm")
m = loader.parse_and_check(state, m_cs, mm, "m")


# We can query the model via an API called ODAPI (Object Diagram API):

from api.od import ODAPI

odapi = ODAPI(state, m, mm)

ls = odapi.get_all_instances("MyAbstractClass", include_subtypes=True)

print("result of get_all_instances:")
print(ls)

# Observing the output above, we see that we got a list of tuples (object_name, UUID).
# We can also modify the model via the same API:

(cc_name, cc_id) = ls[0]
z2 = odapi.create_object("z2", "Z")
odapi.create_link("lnk", "myZ", cc_id, z2)

# And we can observe the modified model:

from concrete_syntax.textual_od.renderer import render_od
from concrete_syntax.common import indent

print()
print("the modified model:")
print(indent(render_od(state, m, mm, hide_names=False), 2))

# BTW, notice that the anonymous link of type 'myZ' from the original model was automatically given a unique name (starting with two underscores).

# The full ODAPI is documented on page 6 of this PDF:
#   http://msdl.uantwerpen.be/people/hv/teaching/MSBDesign/202425/assignments/assignment6.pdf


# On to the next tutorial...
