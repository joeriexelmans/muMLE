import pytest


@pytest.mark.usefixtures("state")
def test_read_dict_keys_no_exists(state):
    assert state.read_dict_keys(100000) is None


@pytest.mark.usefixtures("state")
def test_read_dict_keys_simple(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_dict_keys(a)
    assert l is not None
    assert set(l) == set([c])


@pytest.mark.usefixtures("state")
def test_read_dict_keys_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    g = state.create_node()
    h = state.create_nodevalue("k")
    i = state.create_edge(a, g)
    j = state.create_edge(i, h)
    assert g is not None
    assert h is not None
    assert i is not None
    assert j is not None

    l = state.read_dict_keys(a)
    assert l is not None
    assert set(l) == set([c, h])
