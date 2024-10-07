# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.matcher import mvs_adapter
from transformation.ramify import ramify
from transformation import rewriter
from services.bottom.V0 import Bottom
from services.primitives.integer_type import Integer
from concrete_syntax.plantuml import renderer as plantuml
from concrete_syntax.textual_od import parser, renderer

import sys

def create_integer_node(state, i: int):
    node = state.create_node()
    integer_t = Integer(node, state)
    integer_t.create(i)
    return node

def main():
    state = DevState()
    root = state.read_root() # id: 0

    scd_mm_id = bootstrap_scd(state)
    int_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "Integer")))
    string_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "String")))

    conf = Conformance(state, scd_mm_id, scd_mm_id)
    print("Conformance SCD_MM -> SCD_MM?", conf.check_nominal(log=True))
    print("--------------------------------------")
    print(renderer.render_od(state, scd_mm_id, scd_mm_id, hide_names=False))
    print("--------------------------------------")

    def create_dsl_mm_api():
        # Create DSL MM with SCD API
        dsl_mm_id = state.create_node()
        dsl_mm_scd = SCD(dsl_mm_id, state)
        dsl_mm_scd.create_class("Animal", abstract=True)
        dsl_mm_scd.create_class("Man", min_c=1, max_c=2)
        dsl_mm_scd.create_inheritance("Man", "Animal")
        dsl_mm_scd.create_model_ref("Integer", int_mm_id)
        dsl_mm_scd.create_attribute_link("Man", "Integer", "weight", optional=False)
        dsl_mm_scd.create_class("Bear")
        dsl_mm_scd.create_inheritance("Bear", "Animal")
        dsl_mm_scd.create_association("afraidOf", "Man", "Animal",
            # Every Man afraid of at least one Animal:
            src_min_c=0,
            src_max_c=None,
            tgt_min_c=1,
            tgt_max_c=None,
        )
        dsl_mm_scd.add_constraint("Man", "read_value(element) < 100")
        return dsl_mm_id

    def create_dsl_mm_parser():
        # Create DSL MM with parser
        dsl_mm_cs = """
# Integer:ModelRef
Bear:Class
Animal:Class
    abstract = True
Man:Class
    lower_cardinality = 1
    upper_cardinality = 2
#    constraint = `get_value(get_slot(element, "weight")) < 100`
Man_weight:AttributeLink (Man -> Integer)
    name = "weight"
    optional = False
    constraint = `get_value(get_target(element)) < 100`
afraidOf:Association (Man -> Animal)
    target_lower_cardinality = 1
Man_inh_Animal:Inheritance (Man -> Animal)
Bear_inh_Animal:Inheritance (Bear -> Animal)
sum_of_weights:GlobalConstraint
    constraint = `len(get_all_instances("afraidOf")) <= 1`
"""
        dsl_mm_id = parser.parse_od(state, dsl_mm_cs, mm=scd_mm_id)
        return dsl_mm_id
    
    def create_dsl_m_api():
        # Create DSL M with OD API
        dsl_m_id = state.create_node()
        dsl_m_od = OD(dsl_mm_id, dsl_m_id, state)
        dsl_m_od.create_object("george", "Man")
        dsl_m_od.create_slot("weight", "george",
            dsl_m_od.create_integer_value("george.weight", 80))
        dsl_m_od.create_object("bear1", "Bear")
        dsl_m_od.create_object("bear2", "Bear")
        dsl_m_od.create_link("georgeAfraidOfBear1", "afraidOf", "george", "bear1")
        dsl_m_od.create_link("georgeAfraidOfBear2", "afraidOf", "george", "bear2")
        return dsl_m_id

    def create_dsl_m_parser():
        # Create DSL M with parser
        dsl_m_cs = """
george :Man 
    weight = 80
bear1:Bear
bear2:Bear
:afraidOf (george -> bear1)
:afraidOf (george -> bear2)
"""
        dsl_m_id = parser.parse_od(state, dsl_m_cs, mm=dsl_mm_id)
        return dsl_m_id


    # dsl_mm_id = create_dsl_mm_api()
    dsl_mm_id = create_dsl_mm_parser()

    print("DSL MM:")
    print("--------------------------------------")
    print(renderer.render_od(state, dsl_mm_id, scd_mm_id, hide_names=False))
    print("--------------------------------------")

    conf = Conformance(state, dsl_mm_id, scd_mm_id)
    print("Conformance DSL_MM -> SCD_MM?", conf.check_nominal(log=True))

    # dsl_m_id = create_dsl_m_api()
    dsl_m_id = create_dsl_m_parser()
    print("DSL M:")
    print("--------------------------------------")
    print(renderer.render_od(state, dsl_m_id, dsl_mm_id, hide_names=False))
    print("--------------------------------------")

    conf = Conformance(state, dsl_m_id, dsl_mm_id)
    print("Conformance DSL_M -> DSL_MM?", conf.check_nominal(log=True))

    # RAMify MM
    prefix = "RAM_" # all ramified types can be prefixed to distinguish them a bit more
    ramified_mm_id = ramify(state, dsl_mm_id, prefix)
    ramified_int_mm_id = ramify(state, int_mm_id, prefix)

    # LHS of our rule
    lhs_id = state.create_node()
    lhs_od = OD(ramified_mm_id, lhs_id, state)
    lhs_od.create_object("man", prefix+"Man")
    lhs_od.create_slot(prefix+"weight", "man", lhs_od.create_string_value(f"man.{prefix}weight", 'v < 99'))
    lhs_od.create_object("scaryAnimal", prefix+"Animal")
    lhs_od.create_link("manAfraidOfAnimal", prefix+"afraidOf", "man", "scaryAnimal")

    conf = Conformance(state, lhs_id, ramified_mm_id)
    print("Conformance LHS_M -> RAM_DSL_MM?", conf.check_nominal(log=True))

    # RHS of our rule
    rhs_id = state.create_node()
    rhs_od = OD(ramified_mm_id, rhs_id, state)
    rhs_od.create_object("man", prefix+"Man")
    rhs_od.create_slot(prefix+"weight", "man", rhs_od.create_string_value(f"man.{prefix}weight", 'v + 5'))
    rhs_od.create_object("bill", prefix+"Man")
    rhs_od.create_slot(prefix+"weight", "bill", rhs_od.create_string_value(f"bill.{prefix}weight", '100'))

    rhs_od.create_link("billAfraidOfMan", prefix+"afraidOf", "bill", "man")

    conf = Conformance(state, rhs_id, ramified_mm_id)
    print("Conformance RHS_M -> RAM_DSL_MM?", conf.check_nominal(log=True))

    def render_ramification():
        uml = (""
            # Render original and RAMified meta-models
            + plantuml.render_package("DSL Meta-Model", plantuml.render_class_diagram(state, dsl_mm_id))
            + plantuml.render_package("Int Meta-Model", plantuml.render_class_diagram(state, int_mm_id))
            + plantuml.render_package("RAMified DSL Meta-Model", plantuml.render_class_diagram(state, ramified_mm_id))
            + plantuml.render_package("RAMified Int Meta-Model", plantuml.render_class_diagram(state, ramified_int_mm_id))

            # Render RAMification traceability links
            + plantuml.render_trace_ramifies(state, dsl_mm_id, ramified_mm_id)
            + plantuml.render_trace_ramifies(state, int_mm_id, ramified_int_mm_id)
        )

        # Render pattern
        uml += plantuml.render_package("LHS", plantuml.render_object_diagram(state, lhs_id, ramified_mm_id))
        uml += plantuml.render_trace_conformance(state, lhs_id, ramified_mm_id)

        # Render pattern
        uml += plantuml.render_package("RHS", plantuml.render_object_diagram(state, rhs_id, ramified_mm_id))
        uml += plantuml.render_trace_conformance(state, rhs_id, ramified_mm_id)

        return uml

    def render_all_matches():
        uml = render_ramification()
        # Render host graph (before rewriting)
        uml += plantuml.render_package("Model (before rewrite)", plantuml.render_object_diagram(state, dsl_m_id, dsl_mm_id))
        # Render conformance
        uml += plantuml.render_trace_conformance(state, dsl_m_id, dsl_mm_id)

        print("matching...")
        generator = mvs_adapter.match_od(state, dsl_m_id, dsl_mm_id, lhs_id, ramified_mm_id)
        for name_mapping, color in zip(generator, ["red", "orange"]):
            print("\nMATCH:\n", name_mapping)

            # Render every match
            uml += plantuml.render_trace_match(state, name_mapping, lhs_id, dsl_m_id, color)

        print("DONE")
        return uml

    def render_rewrite():
        uml = render_ramification()

        generator = mvs_adapter.match_od(state, dsl_m_id, dsl_mm_id, lhs_id, ramified_mm_id)
        for name_mapping in generator:
            rewriter.rewrite(state, lhs_id, rhs_id, ramified_mm_id, name_mapping, dsl_m_id, dsl_mm_id)

            conf = Conformance(state, dsl_m_id, dsl_mm_id)
            print("Conformance DSL_M (after rewrite) -> DSL_MM?", conf.check_nominal(log=True))

            # Render match
            uml_match = plantuml.render_trace_match(state, name_mapping, rhs_id, dsl_m_id, 'orange')

            # Stop matching after rewrite
            break

        # Render host graph (after rewriting)
        uml += plantuml.render_package("Model (after rewrite)", plantuml.render_object_diagram(state, dsl_m_id, dsl_mm_id))
        # Render conformance
        uml += plantuml.render_trace_conformance(state, dsl_m_id, dsl_mm_id)

        uml += uml_match

        return uml

    # plantuml_str = render_all_matches()
    # plantuml_str = render_rewrite()

    # print()
    # print("==============================================")

    # print(plantuml_str)


if __name__ == "__main__":
    main()
