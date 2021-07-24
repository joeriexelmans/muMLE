import pytest


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_exists(state):
    l = state.read_reverse_dict(-1, "abc")
    assert l is None


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_node(state):
    a = state.create_node()
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(a, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_nodevalue(state):
    a = state.create_nodevalue(1)
    assert a is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(a, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_not_found_edge(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_edge(a, b)
    assert a is not None
    assert b is not None
    assert c is not None

    # Passing data is not enforced, as the data will be interpreted if necessary
    l = state.read_reverse_dict(c, "abc")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_primitive(state):
    a = state.create_node()
    assert a is not None

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
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_reverse_dict(b, "f")
    assert set(l) == set([a])


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_no_match(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("g")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    l = state.read_reverse_dict(b, "f")
    assert l == []


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_multi(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    g = state.create_node()
    h = state.create_nodevalue("k")
    i = state.create_edge(a, g)
    j = state.create_edge(i, h)
    assert g is not None
    assert h is not None
    assert i is not None
    assert j is not None

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
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    g = state.create_node()
    h = state.create_nodevalue("f")
    i = state.create_edge(g, a)
    j = state.create_edge(i, h)
    assert g is not None
    assert h is not None
    assert i is not None
    assert j is not None

    l = state.read_reverse_dict(a, "f")
    assert set(l) == set([b, g])


@pytest.mark.usefixtures("state")
def test_read_reverse_dict_node_uncertain(state):
    a = state.create_node()
    b = state.create_node()
    c = state.create_nodevalue("f")
    d = state.create_edge(a, b)
    e = state.create_edge(d, c)
    assert a is not None
    assert b is not None
    assert c is not None
    assert d is not None
    assert e is not None

    h = state.create_nodevalue("g")
    i = state.create_edge(d, h)
    assert h is not None
    assert i is not None

    l = state.read_reverse_dict(b, "f")
    assert set(l) == set([a])
