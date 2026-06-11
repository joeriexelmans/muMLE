from typing import Any
from pydantic import BaseModel


class FileUpdate(BaseModel):
    content: Any
    type: str