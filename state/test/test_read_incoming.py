import pytest


@pytest.mark.usefixtures("state")
def test_read_incoming_node_none(state):
    b = state.create_node()
    assert b is not None

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_node_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([c])


@pytest.mark.usefixtures("state")
def test_read_incoming_node_multi(state):
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

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([c, d, e])


@pytest.mark.usefixtures("state")
def test_read_incoming_node_multi_others_unaffected(state):
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

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_edge_none(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_edge_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, a)
    e = state.create_edge(a, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([e])

    l = state.read_incoming(d)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(e)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_edge_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, c)
    e = state.create_edge(b, c)
    f = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None
    assert f is not None

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([c])

    l = state.read_incoming(c)
    assert l is not None
    assert set(l) == set([d, e, f])

    l = state.read_incoming(d)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(e)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_nodevalue_none(state):
    b = state.create_nodevalue(1)
    assert b is not None

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_nodevalue_one(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(b, a)
    assert a is not None
    assert b is not None
    assert c is not None

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([c])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_nodevalue_multi(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(b, a)
    d = state.create_edge(b, a)
    e = state.create_edge(b, a)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_nodevalue_multi_others_unaffected(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(b, a)
    d = state.create_edge(b, a)
    e = state.create_edge(b, a)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    f = state.create_nodevalue(1)
    assert f is not None

    l = state.read_incoming(a)
    assert l is not None
    assert set(l) == set([c, d, e])

    l = state.read_incoming(b)
    assert l is not None
    assert set(l) == set([])

    l = state.read_incoming(f)
    assert l is not None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_incoming_node_deleted(state):
    b = state.create_node()
    assert b is not None

    n = state.delete_node(b)
    assert n is None

    l = state.read_incoming(b)
    assert l is None


@pytest.mark.usefixtures("state")
def test_read_incoming_nodevalue_deleted(state):
    b = state.create_nodevalue(1)
    assert b is not None

    n = state.delete_node(b)
    assert n is None

    l = state.read_incoming(b)
    assert l is None


@pytest.mark.usefixtures("state")
def test_read_incoming_edge_deleted(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    n = state.delete_edge(c)
    assert n is None

    l = state.read_incoming(c)
    assert l is None
