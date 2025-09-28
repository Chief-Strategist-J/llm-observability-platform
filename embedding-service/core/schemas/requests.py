"""Request schemas with validation."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to embed")
    collection: Optional[str] = Field(None, description="Collection name")

class UpsertRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., min_items=1, description="Items to upsert")
    collection: Optional[str] = Field(None, description="Collection name")
    
    @validator('items')
    def validate_items(cls, v):
        for item in v:
            if 'id' not in item:
                raise ValueError("Each item must have an 'id' field")
            if 'text' not in item and 'vector' not in item:
                raise ValueError("Each item must have either 'text' or 'vector' field")
        return v

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Number of results")
    collection: Optional[str] = Field(None, description="Collection name")
    with_payload: bool = Field(True, description="Include payload in results")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum score threshold")

class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Collection name")
    vector_size: int = Field(384, ge=1, le=4096, description="Vector dimensions")
    distance: str = Field("Cosine", description="Distance metric")
    
    @validator('distance')
    def validate_distance(cls, v):
        if v not in ["Cosine", "Dot", "Euclid"]:
            raise ValueError("Distance must be one of: Cosine, Dot, Euclid")
        return v
