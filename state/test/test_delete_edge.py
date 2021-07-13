import pytest


@pytest.mark.usefixtures("state")
def test_delete_edge_no_exists(state):
    e = state.delete_edge(1)
    assert e is None


@pytest.mark.usefixtures("state")
def test_delete_edge_node(state):
    a = state.create_node()
    assert a is not None

    e = state.delete_edge(a)
    assert e is None


@pytest.mark.usefixtures("state")
def test_delete_edge_nodevalue(state):
    a = state.create_nodevalue(1)
    assert a is not None

    e = state.delete_edge(a)
    assert e is None


@pytest.mark.usefixtures("state")
def test_delete_edge_normal(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_edge(c)
    assert n is None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_delete_edge_remove_recursive(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None

    n = state.delete_edge(c)
    assert n is None

    l = state.read_value(a)
    assert l == 1

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(c)
    assert s is None
    assert t is None

    s, t = state.read_edge(d)
    assert s is None
    assert t is None

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_delete_edge_remove_edge_recursive_deep(state):
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

    n = state.delete_edge(d)
    assert n is None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

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


@pytest.mark.usefixtures("state")
def test_delete_edge_remove_edge_recursive_steps(state):
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

    n = state.delete_edge(g)
    assert n is None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([d])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([h])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([d])

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([h, e])

    s, t = state.read_edge(d)
    assert s == a
    assert t == b

    l = state.read_outgoing(d)
    assert l is not None
    assert set(l) == set([e])

    l = state.read_incoming(d)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(e)
    assert s == d
    assert t == c

    l = state.read_outgoing(e)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(e)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(g)
    assert s is None
    assert t is None

    l = state.read_outgoing(g)
    assert l is None

    l = state.read_incoming(g)
    assert l is None

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(h)
    assert s == b
    assert t == c

    n = state.delete_edge(e)
    assert n is None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([d])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([h])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([d])

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([h])

    s, t = state.read_edge(d)
    assert s == a
    assert t == b

    l = state.read_outgoing(d)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(d)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(e)
    assert s is None
    assert t is None

    l = state.read_outgoing(e)
    assert l is None

    l = state.read_incoming(e)
    assert l is None

    s, t = state.read_edge(g)
    assert s is None
    assert t is None

    l = state.read_outgoing(g)
    assert l is None

    l = state.read_incoming(g)
    assert l is None

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(h)
    assert s == b
    assert t == c

    n = state.delete_edge(d)
    assert n is None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

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

    l = state.read_outgoing(d)
    assert l is None

    l = state.read_incoming(d)
    assert l is None

    s, t = state.read_edge(e)
    assert s is None
    assert t is None

    l = state.read_outgoing(e)
    assert l is None

    l = state.read_incoming(e)
    assert l is None

    s, t = state.read_edge(g)
    assert s is None
    assert t is None

    l = state.read_outgoing(g)
    assert l == None

    l = state.read_incoming(g)
    assert l == None

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])

    s, t = state.read_edge(h)
    assert s == b
    assert t == c
