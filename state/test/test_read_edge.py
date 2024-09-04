import pytest


@pytest.mark.usefixtures("state")
def test_read_edge_node(state):
    b = state.create_node()
    assert b != None

    s, t = state.read_edge(b)
    assert s == None
    assert t == None


@pytest.mark.usefixtures("state")
def test_read_edge_no_exists(state):
    s, t = state.read_edge(-1)
    assert s == None
    assert t == None


@pytest.mark.usefixtures("state")
def test_read_edge_nodevalue(state):
    b = state.create_nodevalue(1)
    assert b != None

    s, t = state.read_edge(b)
    assert s == None
    assert t == None


@pytest.mark.usefixtures("state")
def test_read_edge_normal(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b


@pytest.mark.usefixtures("state")
def test_read_edge_edge_to_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(c, d)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b

    s, t = state.read_edge(d)
    assert s == a
    assert t == b

    s, t = state.read_edge(e)
    assert s == c
    assert t == d


@pytest.mark.usefixtures("state")
def test_read_edge_edge_to_node(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b

    s, t = state.read_edge(d)
    assert s == c
    assert t == b


@pytest.mark.usefixtures("state")
def test_read_edge_node_to_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(b, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b

    s, t = state.read_edge(d)
    assert s == b
    assert t == c


@pytest.mark.usefixtures("state")
def test_read_edge_node_to_nodevalue(state):
    a = state.create_node()
    b = state.create_nodevalue(1)
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b


@pytest.mark.usefixtures("state")
def test_read_edge_nodevalue_to_nodevalue(state):
    a = state.create_nodevalue(1)
    b = state.create_nodevalue(1)
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    s, t = state.read_edge(c)
    assert s == a
    assert t == b
