from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"

class NodeType(Enum):
    ENTITY = "Entity"
    CONCEPT = "Concept"
    EVENT = "Event"
    DOCUMENT = "Document"
    CHUNK = "Chunk"

@dataclass
class Chunk:
    text: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class Entity:
    name: str
    entity_type: str
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphNode:
    id: str
    label: NodeType
    properties: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class GraphRelation:
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Memory:
    id: str
    content: str
    memory_type: MemoryType
    importance: float
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryContext:
    query: str
    embedding: Optional[List[float]] = None
    max_hops: int = 3
    limit: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReasoningResult:
    answer: str
    entities: List[Entity]
    relations: List[Relation]
    reasoning_path: List[str]
    confidence: float
    sources: List[str]

@dataclass
class IngestionRequest:
    content: str
    source_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IngestionResponse:
    source_id: str
    chunks_created: int
    entities_extracted: int
    relations_extracted: int
    status: str
