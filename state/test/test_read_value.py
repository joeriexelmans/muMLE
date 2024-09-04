import pytest


@pytest.mark.usefixtures("state")
def test_read_value_different_id_simple(state):
    id1 = state.create_nodevalue(1)
    id2 = state.create_nodevalue(2)
    assert id1 != None
    assert id2 != None

    v1 = state.read_value(id1)
    v2 = state.read_value(id2)
    assert v1 == 1
    assert v2 == 2


@pytest.mark.usefixtures("state")
def test_read_value_integer_ib_negative(state):
    # Just within range
    for i in range(-2 ** 63, -2 ** 63 + 10):
        id1 = state.create_nodevalue(i)
        assert id1 != None

        v = state.read_value(id1)
        assert v == i


@pytest.mark.usefixtures("state")
def test_read_value_integer_ib_zero(state):
    # Nicely within range
    for i in range(-10, 10):
        id1 = state.create_nodevalue(i)
        assert id1 != None

        v = state.read_value(id1)
        assert v == i


@pytest.mark.usefixtures("state")
def test_read_value_integer_ib_positive(state):
    # Just within range
    for i in range(2 ** 63 - 10, 2 ** 63):
        id1 = state.create_nodevalue(i)
        assert id1 != None

        v = state.read_value(id1)
        assert v == i


@pytest.mark.usefixtures("state")
def test_read_value_boolean(state):
    id1 = state.create_nodevalue(True)
    id2 = state.create_nodevalue(False)
    assert id1 != None
    assert id2 != None

    v1 = state.read_value(id1)
    v2 = state.read_value(id2)
    assert v1 == True
    assert v2 == False


@pytest.mark.usefixtures("state")
def test_read_nodevalue_boolean_same(state):
    id1 = state.create_nodevalue(True)
    id2 = state.create_nodevalue(True)
    assert id1 != None
    assert id2 != None

    v1 = state.read_value(id1)
    v2 = state.read_value(id2)
    assert v1 == True
    assert v2 == True


@pytest.mark.usefixtures("state")
def test_read_value_no_exist(state):
    v1 = state.read_value(100000)
    assert v1 == None


@pytest.mark.usefixtures("state")
def test_read_value_no_value(state):
    id1 = state.create_node()
    assert id1 != None

    v1 = state.read_value(id1)
    assert v1 == None
