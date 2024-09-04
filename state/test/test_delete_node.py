import pytest


@pytest.mark.usefixtures("state")
def test_delete_node_no_exists(state):
    n = state.delete_node(-1)
    assert n == None


@pytest.mark.usefixtures("state")
def test_delete_node_no_value(state):
    a = state.create_node()
    assert a != None

    n = state.delete_node(a)
    assert n == None


@pytest.mark.usefixtures("state")
def test_delete_node_value(state):
    a = state.create_nodevalue(1)
    assert a != None

    d = state.read_value(a)
    assert d == 1

    n = state.delete_node(a)
    assert n == None

    d = state.read_value(a)
    assert d == None


@pytest.mark.usefixtures("state")
def test_delete_node_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    n = state.delete_node(c)
    assert n == None


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_outgoing(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    n = state.delete_node(a)
    assert n == None

    d = state.read_value(a)
    assert d == None

    s, t = state.read_edge(c)
    assert s == None
    assert t == None

    d = state.read_outgoing(b)
    assert d != None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_incoming(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(b, a)
    assert a != None
    assert b != None
    assert c != None

    n = state.delete_node(a)
    assert n == None

    d = state.read_value(a)
    assert d == None

    s, t = state.read_edge(c)
    assert s == None
    assert t == None

    d = state.read_outgoing(b)
    assert d != None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_both(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    e = state.create_node()
    f = state.create_edge(e, a)
    assert a != None
    assert b != None
    assert c != None
    assert e != None
    assert f != None

    n = state.delete_node(a)
    assert n == None

    d = state.read_value(a)
    assert d == None

    s, t = state.read_edge(c)
    assert s == None
    assert t == None

    d = state.read_incoming(b)
    assert d != None
    assert set(d) == set([])

    s, t = state.read_edge(f)
    assert s == None
    assert t == None

    d = state.read_outgoing(e)
    assert d != None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_recursive(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None

    n = state.delete_node(a)
    assert n == None

    d = state.read_value(a)
    assert d == None

    s, t = state.read_edge(c)
    assert s == None
    assert t == None

    s, t = state.read_edge(d)
    assert s == None
    assert t == None

    d = state.read_outgoing(b)
    assert d != None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_recursive_deep(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_node()
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    f = state.create_node()
    g = state.create_edge(f, e)
    h = state.create_edge(b, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None
    assert f != None
    assert g != None
    assert h != None

    n = state.delete_node(a)
    assert n == None

    l = state.read_outgoing(a)
    assert l == None

    l = state.read_incoming(a)
    assert l == None

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([h])

    l = state.read_incoming(b)
    assert l != None
    assert set(l) == set([])

    l = state.read_outgoing(c)
    assert l != None
    assert set(l) == set([])

    l = state.read_incoming(c)
    assert l != None
    assert set(l) == set([h])

    s, t = state.read_edge(d)
    assert s == None
    assert t == None

    s, t = state.read_edge(e)
    assert s == None
    assert t == None

    s, t = state.read_edge(g)
    assert s == None
    assert t == None

    l = state.read_outgoing(f)
    assert l != None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l != None
    assert set(l) == set([])

    s, t = state.read_edge(h)
    assert s == b
    assert t == c
