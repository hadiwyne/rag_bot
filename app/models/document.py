from pydantic import BaseModel
from typing import Optional

class DocumentResponse(BaseModel):
    id: str
    filename: str
    size: int
    type: str
    status: str