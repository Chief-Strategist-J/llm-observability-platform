"""Request schemas."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class EmbedRequest(BaseModel):
    text: str
    collection: Optional[str] = None

class UpsertRequest(BaseModel):
    items: List[Dict[str, Any]]
    collection: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    collection: Optional[str] = None
    with_payload: bool = True

class CreateCollectionRequest(BaseModel):
    name: str
    vector_size: int = 384
    distance: str = "Cosine"
