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

def create_integer_node(state, i: int):
    node = state.create_node()
    integer_t = Integer(node, state)
    integer_t.create(i)
    return node

def main():
    state = DevState()
    root = state.read_root() # id: 0

    # Meta-meta-model: a class diagram that describes the language of class diagrams
    scd_mmm_id = bootstrap_scd(state)
    int_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "Integer")))
    string_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "String")))

    # conf = Conformance(state, scd_mmm_id, scd_mmm_id)
    # print("Conformance SCD_MM -> SCD_MM?", conf.check_nominal(log=True))
    # print("--------------------------------------")
    # print(renderer.render_od(state, scd_mmm_id, scd_mmm_id, hide_names=True))
    # print("--------------------------------------")

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
            constraint = ```
                get_value(get_slot(this, "weight")) > 20
            ```;
        }
        Man_weight:AttributeLink (Man -> Integer) {
            name = "weight";
            optional = False;
            constraint = ```
                # this is the same constraint as above, but this time, part of the attributelink itself (and thus shorter)
                tgt = get_target(this)
                tgt_type = get_type_name(tgt)
                get_value(tgt) > 20
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
    dsl_mm_id = parser.parse_od(state, dsl_mm_cs, mm=scd_mmm_id)
    
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

    # print("DSL MM:")
    # print("--------------------------------------")
    # print(renderer.render_od(state, dsl_mm_id, scd_mmm_id, hide_names=True))
    # print("--------------------------------------")

    conf = Conformance(state, dsl_mm_id, scd_mmm_id)
    print("Conformance DSL_MM -> SCD_MM?", conf.check_nominal(log=True))

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
