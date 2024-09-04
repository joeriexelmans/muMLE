import pytest


@pytest.mark.usefixtures("state")
def test_create_edge_invalid_source(state):
    a = -1
    b = state.create_node()
    assert b != None

    e = state.create_edge(a, b)
    assert e == None


@pytest.mark.usefixtures("state")
def test_create_edge_invalid_target(state):
    b = -1
    a = state.create_node()
    assert a != None

    e = state.create_edge(a, b)
    assert e == None


@pytest.mark.usefixtures("state")
def test_create_edge_invalid_both(state):
    a = -1
    b = -1
    e = state.create_edge(a, b)
    assert e == None


@pytest.mark.usefixtures("state")
def test_create_edge_node_to_node(state):
    a = state.create_node()
    assert a != None
    b = state.create_node()
    assert b != None

    edge = state.create_edge(a, b)
    assert edge != None


@pytest.mark.usefixtures("state")
def test_create_edge_multiple(state):
    a = state.create_node()
    assert a != None
    b = state.create_node()
    assert b != None

    edge1 = state.create_edge(a, b)
    assert edge1 != None

    edge2 = state.create_edge(a, b)
    assert edge2 != None

    assert edge1 != edge2


@pytest.mark.usefixtures("state")
def test_create_edge_many(state):
    v = set()
    for i in range(1000):
        a = state.create_node()
        assert a != None
        b = state.create_node()
        assert b != None

        edge = state.create_edge(a, b)
        assert edge != None

        v.add(edge)
    assert len(v) == 1000


@pytest.mark.usefixtures("state")
def test_create_edge_edge_to_node(state):
    a = state.create_node()
    assert a != None
    b = state.create_node()
    assert b != None

    edge1 = state.create_edge(a, b)
    assert edge1 != None

    edge2 = state.create_edge(edge1, b)
    assert edge2 != None

    assert edge1 != edge2


@pytest.mark.usefixtures("state")
def test_create_edge_node_to_edge(state):
    a = state.create_node()
    assert a != None
    b = state.create_node()
    assert b != None

    edge1 = state.create_edge(a, b)
    assert edge1 != None

    edge2 = state.create_edge(a, edge1)
    assert edge2 != None

    assert edge1 != edge2


@pytest.mark.usefixtures("state")
def test_create_edge_edge_to_edge(state):
    a = state.create_node()
    assert a != None
    b = state.create_node()
    assert b != None

    edge1 = state.create_edge(a, b)
    assert edge1 != None

    edge2 = state.create_edge(a, b)
    assert edge2 != None

    assert edge1 != edge2

    edge3 = state.create_edge(edge1, edge2)
    assert edge3 != None


@pytest.mark.usefixtures("state")
def test_create_edge_loop_node(state):
    a = state.create_node()
    assert a != None

    edge = state.create_edge(a, a)
    assert edge != None


@pytest.mark.usefixtures("state")
def test_create_edge_loop_edge(state):
    a = state.create_node()
    assert a != None

    edge1 = state.create_edge(a, a)
    assert edge1 != None

    edge2 = state.create_edge(edge1, edge1)
    assert edge2 != None
