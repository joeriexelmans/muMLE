import pytest


@pytest.mark.usefixtures("state")
def test_read_dict_no_exists(state):
    assert state.read_dict(-1, "abc") == None


@pytest.mark.usefixtures("state")
def test_read_dict_not_found_node(state):
    a = state.create_node()
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict(a, "abc") == None


@pytest.mark.usefixtures("state")
def test_read_dict_not_found_nodevalue(state):
    a = state.create_nodevalue(1)
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict(a, "abc") == None


@pytest.mark.usefixtures("state")
def test_read_dict_not_found_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict(c, "abc") == None


@pytest.mark.usefixtures("state")
def test_read_dict_no_primitive(state):
    a = state.create_node()
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    assert state.read_dict(a, a) == None


@pytest.mark.usefixtures("state")
def test_read_dict_node_simple(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    l = state.read_dict(a, "f")
    assert l == b


@pytest.mark.usefixtures("state")
def test_read_dict_node_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    g = state.create_node()
    h = state.create_nodevalue("k")
    i = state.create_edge(a, g)
    j = state.create_edge(i, h)
    assert g != None
    assert h != None
    assert i != None
    assert j != None

    l = state.read_dict(a, "f")
    assert l == b

    l = state.read_dict(a, "k")
    assert l == g

    assert state.read_dict(a, "l") == None
