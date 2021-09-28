import pytest
from state.pystate import PyState
from state.rdfstate import RDFState
from state.neo4jstate import Neo4jState


@pytest.fixture(params=[
    (PyState,),
    (RDFState, "http://example.org/#"),
#    (Neo4jState,)
])
def state(request):
    if len(request.param) > 1:
        state = request.param[0](*request.param[1:])
    else:
        state = request.param[0]()
    yield state
    if isinstance(state, Neo4jState):
        state.close(clear=True)
