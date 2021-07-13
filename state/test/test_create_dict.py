import pytest


@pytest.mark.usefixtures("state")
def test_create_dict_simple(state):
    id1 = state.create_node()
    id2 = state.create_node()
    assert id1 is not None
    assert id2 is not None

    n = state.create_dict(id1, "abc", id2)
    assert n is None

    v = state.read_dict(id1, "abc")
    assert v == id2


@pytest.mark.usefixtures("state")
def test_create_dict_no_source(state):
    id1 = 100000
    id2 = state.create_node()
    assert id2 is not None

    n = state.create_dict(id1, "abc", id2)
    assert n is None

    v = state.read_dict(id1, "abc")
    assert v is None


@pytest.mark.usefixtures("state")
def test_create_dict_no_target(state):
    id2 = 100000
    id1 = state.create_node()
    assert id1 is not None

    n = state.create_dict(id1, "abc", id2)
    assert n is None

    v = state.read_dict(id1, "abc")
    assert v is None
