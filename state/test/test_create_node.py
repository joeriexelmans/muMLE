import pytest


@pytest.mark.usefixtures("state")
def test_create_node_different_id_simple(state):
    id1 = state.create_node()
    assert id1 != None
    id2 = state.create_node()
    assert id2 != None

    assert id1 != id2


@pytest.mark.usefixtures("state")
def test_create_node_different_id_long(state):
    results = set()
    for i in range(1000):
        v = state.create_node()
        assert v != None
        results.add(v)

    assert len(results) == 1000
