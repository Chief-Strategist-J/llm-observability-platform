from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class Entity:
    name: str
    entity_type: str
    confidence: float
    properties: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    confidence: float
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphNode:
    id: str
    label: NodeType
    properties: dict[str, Any]
    embedding: list[float] | None = None


@dataclass
class GraphRelation:
    source_id: str
    target_id: str
    relation_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    id: str
    content: str
    memory_type: MemoryType
    importance: float
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryContext:
    query: str
    embedding: list[float] | None = None
    max_hops: int = 3
    limit: int = 10
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    answer: str
    entities: list[Entity]
    relations: list[Relation]
    reasoning_path: list[str]
    confidence: float
    sources: list[str]


@dataclass
class IngestionRequest:
    content: str
    source_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionResponse:
    source_id: str
    chunks_created: int
    entities_extracted: int
    relations_extracted: int
    status: str
