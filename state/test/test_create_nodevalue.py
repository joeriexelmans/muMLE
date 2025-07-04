import pytest


@pytest.mark.usefixtures("state")
def test_create_nodevalue_different_id_simple(state):
    id1 = state.create_nodevalue(1)
    id2 = state.create_nodevalue(1)

    assert id1 != None
    assert id2 != None
    assert id1 != id2


@pytest.mark.usefixtures("state")
def test_create_nodevalue_read(state):
    id1 = state.create_nodevalue(1)
    assert id1 != None
    val = state.read_value(id1)
    assert val == 1


@pytest.mark.usefixtures("state")
def test_create_nodevalue_integer_ib_zero(state):
    # Nicely within range
    v = set()
    size = 0
    for i in range(-10, 10):
        id1 = state.create_nodevalue(i)
        assert id1 != None
        size += 1
        v.add(id1)
    assert len(v) == size


@pytest.mark.usefixtures("state")
def test_create_nodevalue_boolean(state):
    id1 = state.create_nodevalue(True)
    id2 = state.create_nodevalue(False)

    assert id1 != None
    assert id2 != None
    assert id1 != id2


@pytest.mark.usefixtures("state")
def test_create_nodevalue_boolean_same(state):
    id1 = state.create_nodevalue(True)
    id2 = state.create_nodevalue(True)

    assert id1 != None
    assert id2 != None
    assert id1 != id2


@pytest.mark.usefixtures("state")
def test_create_nodevalue_float_keeps_type(state):
    id1 = state.create_nodevalue(0.0)
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == float
    assert v == 0.0


@pytest.mark.usefixtures("state")
def test_create_nodevalue_string_empty(state):
    id1 = state.create_nodevalue("")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == ""


@pytest.mark.usefixtures("state")
def test_create_nodevalue_string_normal(state):
    id1 = state.create_nodevalue("ABC")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == "ABC"


@pytest.mark.usefixtures("state")
def test_create_nodevalue_string_not_parsed(state):
    id1 = state.create_nodevalue("1")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == "1"

    id1 = state.create_nodevalue("1.0")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == "1.0"

    id1 = state.create_nodevalue("-1.0")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == "-1.0"

    id1 = state.create_nodevalue("True")
    assert id1 != None

    v = state.read_value(id1)
    assert type(v) == str
    assert v == "True"


@pytest.mark.usefixtures("state")
def test_create_nodevalue_junk(state):
    class Unknown(object):
        pass

    n = state.create_nodevalue(Unknown())
    assert n == None


@pytest.mark.usefixtures("state")
def test_create_nodevalue_type_type(state):
    id1 = state.create_nodevalue(("Type",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("Type",)


@pytest.mark.usefixtures("state")
def test_create_nodevalue_integer_type(state):
    id1 = state.create_nodevalue(("Integer",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("Integer",)


@pytest.mark.usefixtures("state")
def test_create_nodevalue_float_type(state):
    id1 = state.create_nodevalue(("Float",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("Float",)


@pytest.mark.usefixtures("state")
def test_create_nodevalue_boolean_type(state):
    id1 = state.create_nodevalue(("Boolean",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("Boolean",)


@pytest.mark.usefixtures("state")
def test_create_nodevalue_string_type(state):
    id1 = state.create_nodevalue(("String",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("String",)


@pytest.mark.usefixtures("state")
def test_create_nodevalue_invalid_type(state):
    id1 = state.create_nodevalue(("Class",))
    assert id1 == None


@pytest.mark.usefixtures("state")
def test_create_nodevalue_bytes_type(state):
    id1 = state.create_nodevalue(("Bytes",))
    assert id1 != None

    v = state.read_value(id1)
    assert v == ("Bytes",)