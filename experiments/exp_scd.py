# Simple Class Diagram experiment

from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
from uuid import UUID
from services.scd import SCD
from framework.conformance import Conformance
from services.od import OD
from transformation.matcher import mvs_adapter
from transformation.ramify import ramify
from transformation.cloner import clone_od
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

    # conf = Conformance(state, scd_mm_id, scd_mm_id)
    # print("Conformance SCD_MM -> SCD_MM?", conf.check_nominal(log=True))
    # print("--------------------------------------")
    # print(renderer.render_od(state, scd_mm_id, scd_mm_id, hide_names=True))
    # print("--------------------------------------")

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
            Animal:Class {
                abstract = True;
            }
            Man:Class {
                lower_cardinality = 1;
                upper_cardinality = 2;
                constraint = `get_value(get_slot(element, "weight")) > 20`;
            }
            Man_weight:AttributeLink (Man -> Integer) {
                name = "weight";
                optional = False;
                constraint = ```
                    # this is the same constraint as above, but this time, part of the attributelink itself (and thus shorter)
                    node = get_target(element)
                    get_value(node) > 20
                ```;
            }
            afraidOf:Association (Man -> Animal) {
                target_lower_cardinality = 1;
            }
            :Inheritance (Man -> Animal)
            :Inheritance (Bear -> Animal)

            not_too_fat:GlobalConstraint {
                constraint = ```
                    # total weight of all men low enough
                    total_weight = 0
                    for man_name, man_id in get_all_instances("Man"):
                        total_weight += get_value(get_slot(man_id, "weight"))
                    total_weight < 85
                ```;
            }
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
            george:Man {
                weight = 80;
            }
            bear1:Bear
            bear2:Bear
            :afraidOf (george -> bear1)
            :afraidOf (george -> bear2)
        """
        dsl_m_id = parser.parse_od(state, dsl_m_cs, mm=dsl_mm_id)
        return dsl_m_id


    # dsl_mm_id = create_dsl_mm_api()
    dsl_mm_id = create_dsl_mm_parser()

    # print("DSL MM:")
    # print("--------------------------------------")
    # print(renderer.render_od(state, dsl_mm_id, scd_mm_id, hide_names=True))
    # print("--------------------------------------")

    conf = Conformance(state, dsl_mm_id, scd_mm_id)
    print("Conformance DSL_MM -> SCD_MM?", conf.check_nominal(log=True))

    # dsl_m_id = create_dsl_m_api()
    dsl_m_id = create_dsl_m_parser()
    # print("DSL M:")
    # print("--------------------------------------")
    # print(renderer.render_od(state, dsl_m_id, dsl_mm_id, hide_names=True))
    # print("--------------------------------------")

    conf = Conformance(state, dsl_m_id, dsl_mm_id)
    print("Conformance DSL_M -> DSL_MM?", conf.check_nominal(log=True))

    # RAMify MM
    prefix = "RAM_" # all ramified types can be prefixed to distinguish them a bit more
    ramified_mm_id = ramify(state, dsl_mm_id, prefix)
    ramified_int_mm_id = ramify(state, int_mm_id, prefix)

    # LHS - pattern to match

    # TODO: enable more powerful constraints
    lhs_cs = f"""
        # object to match
        man:{prefix}Man {{
            # match only men heavy enough
            {prefix}weight = `v > 60`;
        }}

        # object to delete
        scaryAnimal:{prefix}Animal

        # link to delete
        manAfraidOfAnimal:{prefix}afraidOf (man -> scaryAnimal)
    """
    lhs_id = parser.parse_od(state, lhs_cs, mm=ramified_mm_id)


    conf = Conformance(state, lhs_id, ramified_mm_id)
    print("Conformance LHS_M -> RAM_DSL_MM?", conf.check_nominal(log=True))

    # RHS of our rule

    # TODO: enable more powerful actions
    rhs_cs = f"""
        # matched object
        man:{prefix}Man {{
            # man gains weight
            {prefix}weight = `v + 5`;
        }}

        # object to create
        bill:{prefix}Man {{
            {prefix}weight = `100`;
        }}

        # link to create
        billAfraidOfMan:{prefix}afraidOf (bill -> man)
    """
    rhs_id = parser.parse_od(state, rhs_cs, mm=ramified_mm_id)

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
        for match, color in zip(generator, ["red", "orange"]):
            print("\nMATCH:\n", match)

            # Render every match
            uml += plantuml.render_trace_match(state, match, lhs_id, dsl_m_id, color)

        print("DONE")
        return uml

    def render_rewrite():
        uml = render_ramification()

        # Render host graph (before rewriting)
        uml += plantuml.render_package("Model (before rewrite)", plantuml.render_object_diagram(state, dsl_m_id, dsl_mm_id))
        # Render conformance
        uml += plantuml.render_trace_conformance(state, dsl_m_id, dsl_mm_id)

        generator = mvs_adapter.match_od(state, dsl_m_id, dsl_mm_id, lhs_id, ramified_mm_id)
        for i, (match, color) in enumerate(zip(generator, ["red", "orange"])):
            uml += plantuml.render_trace_match(state, match, lhs_id, dsl_m_id, color)

            # rewrite happens in-place (which sucks), so we will only modify a clone:
            snapshot_dsl_m_id = clone_od(state, dsl_m_id, dsl_mm_id)
            rewriter.rewrite(state, lhs_id, rhs_id, ramified_mm_id, match, snapshot_dsl_m_id, dsl_mm_id)

            conf = Conformance(state, snapshot_dsl_m_id, dsl_mm_id)
            print(f"Conformance DSL_M (after rewrite {i}) -> DSL_MM?", conf.check_nominal(log=True))

            # Render host graph (after rewriting)
            uml += plantuml.render_package(f"Model (after rewrite {i})", plantuml.render_object_diagram(state, snapshot_dsl_m_id, dsl_mm_id))
            # Render match
            uml += plantuml.render_trace_match(state, match, rhs_id, snapshot_dsl_m_id, color)
            # Render conformance
            uml += plantuml.render_trace_conformance(state, snapshot_dsl_m_id, dsl_mm_id)

        return uml

    # plantuml_str = render_all_matches()
    plantuml_str = render_rewrite()

    print()
    print("==============================================")
    print("BEGIN PLANTUML")
    print("==============================================")

    print(plantuml_str)

    print("==============================================")
    print("END PLANTUML")
    print("==============================================")

if __name__ == "__main__":
    main()
