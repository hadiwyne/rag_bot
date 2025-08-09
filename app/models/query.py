from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class QueryRequest(BaseModel):
    query: str
    max_results: int = 3

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float