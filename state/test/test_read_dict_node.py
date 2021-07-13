import pytest


@pytest.mark.usefixtures("state")
def test_read_dict_node_no_exists(state):
    assert state.read_dict_node(-1, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_node_not_found_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_node(c, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_node_no_primitive(state):
    a = state.create_node()
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_node(a, a) is None


@pytest.mark.usefixtures("state")
def test_read_dict_node_node_simple(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_node()
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_dict_node(a, c)
    assert l == b


@pytest.mark.usefixtures("state")
def test_read_dict_node_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_node()
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    g = state.create_node()
    h = state.create_node()
    i = state.create_edge(a, g)
    j = state.create_edge(i, h)
    assert g is not None
    assert h is not None
    assert i is not None
    assert j is not None

    l = state.read_dict_node(a, c)
    assert l == b

    l = state.read_dict_node(a, h)
    assert l == g
