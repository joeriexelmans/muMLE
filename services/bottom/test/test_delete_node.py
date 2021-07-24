import pytest


@pytest.mark.usefixtures("state")
def test_delete_node_no_exists(state):
    n = state.delete_node(-1)
    assert n is None


@pytest.mark.usefixtures("state")
def test_delete_node_no_value(state):
    a = state.create_node()
    assert a is not None

    n = state.delete_node(a)
    assert n is None


@pytest.mark.usefixtures("state")
def test_delete_node_value(state):
    a = state.create_nodevalue(1)
    assert a is not None

    d = state.read_value(a)
    assert d == 1

    n = state.delete_node(a)
    assert n is None

    d = state.read_value(a)
    assert d is None


@pytest.mark.usefixtures("state")
def test_delete_node_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_node(c)
    assert n is None


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_outgoing(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_node(a)
    assert n is None

    d = state.read_value(a)
    assert d is None

    s, t = state.read_edge(c)
    assert s is None
    assert t is None

    d = state.read_outgoing(b)
    assert d is not None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_incoming(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(b, a)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_node(a)
    assert n is None

    d = state.read_value(a)
    assert d is None

    s, t = state.read_edge(c)
    assert s is None
    assert t is None

    d = state.read_outgoing(b)
    assert d is not None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_both(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    e = state.create_node()
    f = state.create_edge(e, a)
    assert a is not None
    assert b is not None
    assert c is not None
    assert e is not None
    assert f is not None

    n = state.delete_node(a)
    assert n is None

    d = state.read_value(a)
    assert d is None

    s, t = state.read_edge(c)
    assert s is None
    assert t is None

    d = state.read_incoming(b)
    assert d is not None
    assert set(d) == set([])

    s, t = state.read_edge(f)
    assert s is None
    assert t is None

    d = state.read_outgoing(e)
    assert d is not None
    assert set(d) == set([])


@pytest.mark.usefixtures("state")
def test_delete_node_remove_edge_recursive(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None

    n = state.delete_node(a)
    assert n is None

    d = state.read_value(a)
    assert d is None

    s, t = state.read_edge(c)
    assert s is None
    assert t is None

    s, t = state.read_edge(d)
    assert s is None
    assert t is None

    d = state.read_outgoing(b)
    assert d is not None
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
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None
    assert f is not None
    assert g is not None
    assert h is not None

    n = state.delete_node(a)
    assert n is None

    l = state.read_outgoing(a)
    assert l is None

    l = state.read_incoming(a)
    assert l is None

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([h])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([h])

    s, t = state.read_edge(d)
    assert s is None
    assert t is None

    s, t = state.read_edge(e)
    assert s is None
    assert t is None

    s, t = state.read_edge(g)
    assert s is None
    assert t is None

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(h)
    assert s == b
    assert t == c
