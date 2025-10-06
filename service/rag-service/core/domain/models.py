"""Domain models for RAG service.

This module contains data classes representing the core domain entities for the
Retrieval-Augmented Generation service.

"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Chunk:
    """
    Represents a chunk of text content with metadata.
    """

    id: str
    text: str
    metadata: dict[str, Any]


@dataclass
class SearchResult:
    """
    Represents a search result with chunk and similarity score.
    """

    chunk: Chunk
    score: float


@dataclass
class QueryRequest:
    """
    Represents a search query request.
    """

    query: str
    limit: int = 5
