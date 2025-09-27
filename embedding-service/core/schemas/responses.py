"""Response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "embedding-service"

class EmbedResponse(BaseModel):
    vector: List[float]
    dimension: int

class SearchResult(BaseModel):
    id: str
    score: float
    payload: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

class StatusResponse(BaseModel):
    success: bool
    message: str
