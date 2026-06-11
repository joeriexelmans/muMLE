from pydantic import BaseModel, RootModel
from typing import List, Optional, Dict, Any

# --- Data models ---
class Position(BaseModel):
    x: float
    y: float

class Node(BaseModel):
    id: str
    height: int
    width: int
    position: Position
    type: str

    ports: dict[str, list]
    meta: dict

class Edge(BaseModel):
    id: str
    source: str
    sourceHandle: Optional[str] = None
    target: str
    targetHandle: Optional[str] = None

class DataTypes(BaseModel):
    name: str
    # elements: Dict[str, str]

class Graph(BaseModel):
    nodes: List[Node] = []
    edges: List[Edge] = []
    # datatypes: List[DataTypes] = []

from pydantic import BaseModel
from typing import Optional


class CreateProcessResponse(BaseModel):
    process_id: str


class StepResponse(BaseModel):
    status: str
    state: Optional[dict] = None


class SaveStateResponse(BaseModel):
    state: dict

class NodeModel(RootModel[Dict[str, Dict[str, object]]]):
    pass

class EdgeItem(BaseModel):
    _source: str
    _target: str
    params: Dict[str, Any]

class EdgeModel(RootModel[List[EdgeItem]]):
    pass

from pydantic import BaseModel, RootModel, Field
from typing import Dict, Any, List


class EdgeItem(BaseModel):
    source: str = Field(alias="_source")
    target: str = Field(alias="_target")
    params: Dict[str, Any] = Field(default_factory=dict)


class EdgesModel(RootModel[List[EdgeItem]]):
    pass
