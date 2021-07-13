import pytest


@pytest.mark.usefixtures("state")
def test_read_dict_edge_no_exists(state):
    assert state.read_dict_edge(-1, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_edge_not_found_node(state):
    a = state.create_node()
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_edge(a, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_edge_not_found_nodevalue(state):
    a = state.create_nodevalue(1)
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_edge(a, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_edge_not_found_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_edge(c, "abc") is None


@pytest.mark.usefixtures("state")
def test_read_dict_edge_no_primitive(state):
    a = state.create_node()
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict_edge(a, a) is None


@pytest.mark.usefixtures("state")
def test_read_dict_edge_node_simple(state):
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

    l = state.read_dict_edge(a, "f")
    assert l == d


@pytest.mark.usefixtures("state")
def test_read_dict_edge_node_multi(state):
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

    l = state.read_dict_edge(a, "f")
    assert l == d

    l = state.read_dict_edge(a, "k")
    assert l == i

    assert state.read_dict_edge(a, "l") is None
