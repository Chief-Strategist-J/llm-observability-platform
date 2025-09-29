from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Chunk:
    id: str
    text: str
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    chunk: Chunk
    score: float

@dataclass
class QueryRequest:
    query: str
    limit: int = 5
