# Consider the following Petri Net language meta-model:

mm_cs = """
    Place:Class
    Transition:Class

    Place_tokens:AttributeLink (Place -> Integer) {
        optional = False;
        name = "tokens";
        constraint = `get_value(get_target(this)) >= 0`;
    }

    P2T:Association (Place -> Transition)
    T2P:Association (Transition -> Place)

    P2T_weight:AttributeLink (P2T -> Integer) {
        optional = False;
        name = "weight";
        constraint = `get_value(get_target(this)) >= 0`;
    }

    T2P_weight:AttributeLink (T2P -> Integer) {
        optional = False;
        name = "weight";
        constraint = `get_value(get_target(this)) >= 0`;
    }
"""

# We now create the following Petri Net:
#  https://upload.wikimedia.org/wikipedia/commons/4/4d/Two-boundedness-cb.png

m_cs = """
    p1:Place  { tokens = 0; }
    p2:Place  { tokens = 0; }
    cp1:Place { tokens = 2; }
    cp2:Place { tokens = 2; }

    t1:Transition
    t2:Transition
    t3:Transition

    :T2P (t1  -> p1)  { weight = 1; }
    :P2T (p1  -> t2)  { weight = 1; }
    :T2P (t2  -> cp1) { weight = 1; }
    :P2T (cp1 -> t1)  { weight = 1; }

    :T2P (t2  -> p2)  { weight = 1; }
    :P2T (p2  -> t3)  { weight = 1; }
    :T2P (t3  -> cp2) { weight = 1; }
    :P2T (cp2 -> t2)  { weight = 1; }
"""

# The usual...

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from util import loader
from transformation.ramify import ramify
from transformation.matcher import match_od
from transformation.cloner import clone_od
from transformation import rewriter
from concrete_syntax.textual_od.renderer import render_od
from concrete_syntax.common import indent
from api.od import ODAPI

state = DevState()
mmm = bootstrap_scd(state)
mm = loader.parse_and_check(state, mm_cs, mmm, "mm")
m = loader.parse_and_check(state, m_cs, mm, "m")

mm_ramified = ramify(state, mm)


# We will now implement Petri Net operational semantics by means of model transformation.


# Look for any transition
lhs_transition_cs = """
    t:RAM_Transition
"""

# A transition is disabled if it has an incoming arc (P2T) from a place with 0 tokens:
lhs_transition_disabled_cs = """
    t:RAM_Transition
    p:RAM_Place
    :RAM_P2T (p -> t) {
        condition = ```
            place = get_source(this)
            tokens = get_slot_value(place, "tokens")
            weight = get_slot_value(this, "weight")
            tokens < weight # True means: cannot fire
        ```;
    }
"""

lhs_transition = loader.parse_and_check(state, lhs_transition_cs, mm_ramified, "lhs_transition")
lhs_transition_disabled = loader.parse_and_check(state, lhs_transition_disabled_cs, mm_ramified, "lhs_transition_disabled")

# We write a generator function, that yields all enabled transitions.
# Notice that we nest two calls to 'match_od', and the result of the first call is passed as a pivot to the second:

def find_enabled_transitions(m):
    for match in match_od(state, m, mm, lhs_transition, mm_ramified):
        for match_nac in match_od(state, m, mm, lhs_transition_disabled, mm_ramified, pivot=match):
            # transition is disabled
            break # find next transition
        else:
            # transition is enabled
            yield match


enabled = list(find_enabled_transitions(m))
print("enabled PN transitions:", enabled)


# To fire a transition, decrement the number of tokens of every incoming place:

lhs_incoming_cs = """
    t:RAM_Transition
    inplace:RAM_Place {
        RAM_tokens = `True`; # this needs to be here, otherwise, the rewriter will try to create a new attribute rather than update the existing one
    }
    inarc:RAM_P2T (inplace -> t)
"""
rhs_incoming_cs = """
    t:RAM_Transition
    inplace:RAM_Place {
        RAM_tokens = ```
            weight = get_slot_value(matched("inarc"), "weight")
            print("adding", weight, "tokens to", get_name(this))
            get_value(this) - weight
        ```;
    }
    inarc:RAM_P2T (inplace -> t)
"""

# And increment for every outgoing place:

lhs_outgoing_cs = """
    t:RAM_Transition
    outplace:RAM_Place {
        RAM_tokens = `True`; # this needs to be here, otherwise, the rewriter will try to create a new attribute rather than update the existing one
    }
    outarc:RAM_T2P (t -> outplace)
"""
rhs_outgoing_cs = """
    t:RAM_Transition
    outplace:RAM_Place {
        RAM_tokens = ```
            weight = get_slot_value(matched("outarc"), "weight")
            print("removing", weight, "tokens from", get_name(this))
            get_value(this) + weight
        ```;
    }
    outarc:RAM_T2P (t -> outplace)
"""

lhs_incoming = loader.parse_and_check(state, lhs_incoming_cs, mm_ramified, "lhs_incoming")
rhs_incoming = loader.parse_and_check(state, rhs_incoming_cs, mm_ramified, "rhs_incoming")
lhs_outgoing = loader.parse_and_check(state, lhs_outgoing_cs, mm_ramified, "lhs_outgoing")
rhs_outgoing = loader.parse_and_check(state, rhs_outgoing_cs, mm_ramified, "rhs_outgoing")

def fire_transition(m, transition_match):
    print("firing transition:", transition_match['t'])
    for match_incoming in match_od(state, m, mm, lhs_incoming, mm_ramified, pivot=transition_match):
        rewriter.rewrite(state, lhs_incoming, rhs_incoming, mm_ramified, match_incoming, m, mm)
    for match_outgoing in match_od(state, m, mm, lhs_outgoing, mm_ramified, pivot=transition_match):
        rewriter.rewrite(state, lhs_outgoing, rhs_outgoing, mm_ramified, match_outgoing, m, mm)

def show_petri_net(m):
    odapi = ODAPI(state, m, mm)
    p1 = odapi.get_slot_value(odapi.get("p1"), "tokens")
    p2 = odapi.get_slot_value(odapi.get("p2"), "tokens")
    cp1 = odapi.get_slot_value(odapi.get("cp1"), "tokens")
    cp2 = odapi.get_slot_value(odapi.get("cp2"), "tokens")
    return f"""
     t1                   t2                   t3  
     ┌─┐        p1        ┌─┐        p2        ┌─┐ 
     │ │        ---       │ │        ---       │ │ 
     │ ├─────► ( {p1} )─────►│ │─────► ( {p2} )─────►│ │ 
     └─┘        ---       └─┘        ---       └─┘ 
      ▲                   │ ▲                   │  
      │                   │ │                   │  
      │                   │ │                   │  
      │                   │ │                   │  
      │        ---        │ │       ---         │  
      └───────( {cp1} )◄──────┘ └──────( {cp2} )◄───────┘  
               ---                  ---            
               cp1                  cp2            """

# Let's see if it works:
while len(enabled) > 0:
    print(show_petri_net(m))
    print("\nenabled PN transitions:", enabled)
    print("press ENTER to fire", enabled[0]['t'])
    input()
    fire_transition(m, enabled[0])
    enabled = list(find_enabled_transitions(m))
