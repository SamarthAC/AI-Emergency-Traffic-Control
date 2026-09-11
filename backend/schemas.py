from typing import Any, Dict
from pydantic import BaseModel

class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any]
