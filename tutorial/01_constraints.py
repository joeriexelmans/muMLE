# We now make our meta-model more interesting by adding a 'price' attribute to B, and constraints to it.

mm_cs = """
    # class named 'A':
    A:Class

    # class named 'B':
    B:Class {
        constraint = ```
            # Price must be less than 100
            get_value(get_slot(this, "price")) < 100 
        ```;
    }

    # 'B' has an attribute 'price':
    B_price:AttributeLink (B -> Integer) {
        name = "price";
        optional = False;
    }

    # An association from 'A' to 'B':
    a2b:Association (A -> B) {
        # Every 'A' must be associated with at least one 'B'
        target_lower_cardinality = 1;
    }

    totalPriceLessThan500:GlobalConstraint {
        constraint = ```
            total_price = 0;
            for b_name, b_id in get_all_instances("B"):
                total_price += get_value(get_slot(b_id, "price"))
            total_price < 500
        ```;
    }
"""

####
# Note: The name 'B_price' follows a fixed format: <class_name>_<attribute_name>.
#  This format must be followed!
####

# We update our model to include a price:

m_cs = """
    myA:A

    myB:B {
        price = 1000;
    }

    myLnk:a2b (myA -> myB)
"""


# And do a conformance check:

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od import parser
from framework.conformance import Conformance, render_conformance_check_result

state = DevState()
print("Loading meta-meta-model...")
mmm = bootstrap_scd(state)
print("OK")

print()
print("Parsing meta-model...")
mm = parser.parse_od(
    state,
    m_text=mm_cs, # the string of text to parse
    mm=mmm, # the meta-model of class diagrams (= our meta-meta-model)
)
print("OK")

print()
print("Parsing model...")
m = parser.parse_od(
    state,
    m_text=m_cs,
    mm=mm, # this time, the meta-model is the previous model we parsed
)
print("OK")

print()
print("Is our model a valid instance of our meta model?")
conf = Conformance(state, m, mm)
print(render_conformance_check_result(conf.check_nominal()))

# Can you fix the constraint violation?


