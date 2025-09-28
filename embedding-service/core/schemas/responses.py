"""Response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "embedding-service"
    version: str = "1.0.0"

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
    query_time_ms: Optional[float] = None

class StatusResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    code: int = 500
