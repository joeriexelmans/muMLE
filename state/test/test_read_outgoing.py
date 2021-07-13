import pytest


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_none(state):
    b = state.create_node()
    assert b is not None

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_multi_others_unaffected(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    f = state.create_node()
    assert f is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_none(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, a)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([d])

    l = state.read_outgoing(d)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, a)
    e = state.create_edge(c, b)
    f = state.create_edge(c, d)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None
    assert f is not None

    l = state.read_outgoing(c)
    assert l is not None
    assert set(l) == set([d, e, f])

    l = state.read_outgoing(d)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(e)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_none(state):
    b = state.create_nodevalue(1)
    assert b is not None

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_one(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_multi(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_multi_others_unaffected(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    f = state.create_nodevalue(1)
    assert f is not None

    l = state.read_outgoing(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l is not None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_deleted(state):
    b = state.create_node()
    assert b is not None

    n = state.delete_node(b)
    assert n is None

    l = state.read_outgoing(b)
    assert l is None


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_deleted(state):
    b = state.create_nodevalue(1)
    assert b is not None

    n = state.delete_node(b)
    assert n is None

    l = state.read_outgoing(b)
    assert l is None


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_deleted(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_edge(c)
    assert n is None

    l = state.read_outgoing(c)
    assert l is None
