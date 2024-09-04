import pytest


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_exists(state):
    l = state.read_reverse_dict(-1, "abc")
    assert l == None


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_node(state):
    a = state.create_node()
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(a, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_nodevalue(state):
    a = state.create_nodevalue(1)
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(a, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a != None
    assert b != None
    assert c != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(c, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_primitive(state):
    a = state.create_node()
    assert a != None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(a, a)
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_simple(state):
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

    l = state.read_reverse_dict(b, "f")
    assert set(l) == set([a])


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_match(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("g")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    l = state.read_reverse_dict(b, "f")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_multi(state):
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

    l = state.read_reverse_dict(b, "f")
    assert set(l) == set([a])

    l = state.read_reverse_dict(g, "k")
    assert set(l) == set([a])

    l = state.read_reverse_dict(a, "l")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_multi_ambiguous(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(b, a)
    e = state.create_edge(d, c)
    assert a != None
    assert b != None
    assert c != None
    assert d != None
    assert e != None

    g = state.create_node()
    h = state.create_nodevalue("f")
    i = state.create_edge(g, a)
    j = state.create_edge(i, h)
    assert g != None
    assert h != None
    assert i != None
    assert j != None

    l = state.read_reverse_dict(a, "f")
    assert set(l) == set([b, g])


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_uncertain(state):
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

    h = state.create_nodevalue("g")
    i = state.create_edge(d, h)
    assert h != None
    assert i != None

    l = state.read_reverse_dict(b, "f")
    assert set(l) == set([a])
