from bootstrap.scd import bootstrap_scd
from concrete_syntax.textual_od.parser import parse_od
from framework.conformance import Conformance
from state.devstate import DevState


def test_association_rejects_invalid_target_type():
    state = DevState()
    scd = bootstrap_scd(state)
    metamodel = parse_od(state, """
        A:Class
        B:Class
        a2b:Association (A -> B)
    """, scd)
    model = parse_od(state, """
        source:A
        wrong_target:A
        link:a2b (source -> wrong_target)
    """, metamodel)

    errors = Conformance(state, model, metamodel).check_link_typing()

    assert errors == ["Invalid target type 'A' for link 'link:a2b'"], errors


def test_association_rejects_unrelated_target_type():
    state = DevState()
    scd = bootstrap_scd(state)
    metamodel = parse_od(state, """
        A:Class
        B:Class
        C:Class
        a2b:Association (A -> B)
    """, scd)
    model = parse_od(state, """
        source:A
        wrong_target:C
        link:a2b (source -> wrong_target)
    """, metamodel)

    errors = Conformance(state, model, metamodel).check_link_typing()

    assert errors == ["Invalid target type 'C' for link 'link:a2b'"], errors
