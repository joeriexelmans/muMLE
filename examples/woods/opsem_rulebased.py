### Operational Semantics - defined by rule-based model transformation ###

from transformation.rule import Rule, RuleMatcherRewriter, PriorityActionGenerator
from transformation.ramify import ramify
from util import loader

import os
THIS_DIR = os.path.dirname(__file__)

get_filename = lambda rule_name, kind: f"{THIS_DIR}/rules/r_{rule_name}_{kind}.od"

def get_action_generator(state, rt_mm):
    rt_mm_ramified = ramify(state, rt_mm)

    matcher_rewriter = RuleMatcherRewriter(state, rt_mm, rt_mm_ramified)

    rules0_dict = loader.load_rules(state, get_filename, rt_mm_ramified, ["hungry_bear_dies"])
    rules1_dict = loader.load_rules(state, get_filename, rt_mm_ramified, ["advance_time", "attack"]) 

    generator = PriorityActionGenerator(matcher_rewriter, [
        rules0_dict, # highest priority
        rules1_dict, # lowest priority
    ])

    return generator
