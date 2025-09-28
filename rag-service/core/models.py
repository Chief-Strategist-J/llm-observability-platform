from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Document:
    id: str
    text: str
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]
