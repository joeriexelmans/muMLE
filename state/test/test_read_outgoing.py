import pytest


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_none(state):
    b = state.create_node()
    assert b != None

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_multi_others_unaffected(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    f = state.create_node()
    assert f != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_none(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    l = state.read_outgoing(c)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_one(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, a)
    assert a != None
    assert b != None
    assert c != None
    assert d != None

    l = state.read_outgoing(c)
    assert l != None
    assert set(l) == set([d])

    l = state.read_outgoing(d)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(c, a)
    e = state.create_edge(c, b)
    f = state.create_edge(c, d)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None
    assert f != None

    l = state.read_outgoing(c)
    assert l != None
    assert set(l) == set([d, e, f])

    l = state.read_outgoing(d)
    assert l != None
    assert set(l) == set([])

    l = state.read_outgoing(e)
    assert l != None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_none(state):
    b = state.create_nodevalue(1)
    assert b != None

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_one(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_multi(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_multi_others_unaffected(state):
    a = state.create_nodevalue(1)
    b = state.create_node()
    c = state.create_edge(a, b)
    d = state.create_edge(a, b)
    e = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    f = state.create_nodevalue(1)
    assert f != None

    l = state.read_outgoing(a)
    assert l != None
    assert set(l) == set([c, d, e])

    l = state.read_outgoing(b)
    assert l != None
    assert set(l) == set([])

    l = state.read_outgoing(f)
    assert l != None
    assert set(l) == set([])


@pytest.mark.usefixtures("state")
def test_read_outgoing_node_deleted(state):
    b = state.create_node()
    assert b != None

    n = state.delete_node(b)
    assert n == None

    l = state.read_outgoing(b)
    assert l == None


@pytest.mark.usefixtures("state")
def test_read_outgoing_nodevalue_deleted(state):
    b = state.create_nodevalue(1)
    assert b != None

    n = state.delete_node(b)
    assert n == None

    l = state.read_outgoing(b)
    assert l == None


@pytest.mark.usefixtures("state")
def test_read_outgoing_edge_deleted(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    n = state.delete_edge(c)
    assert n == None

    l = state.read_outgoing(c)
    assert l == None
