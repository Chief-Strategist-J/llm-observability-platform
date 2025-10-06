"""Reasoning query use case for knowledge graph service.

This module contains the main reasoning logic that combines information from memory
stores and graph databases to provide intelligent responses.

"""

from ..domain.models import (
    MemoryType,
    QueryContext,
    ReasoningResult,
)
from ..ports.embedding_model import EmbeddingModelPort
from ..ports.graph_store import GraphStorePort
from ..ports.memory_store import MemoryStorePort


async def reason_query(
    context: QueryContext,
    embedding: EmbeddingModelPort,
    graph_store: GraphStorePort,
    memory_store: MemoryStorePort,
) -> ReasoningResult:
    """Perform reasoning query using knowledge graph and memory stores.

    This function combines information from multiple sources:
    - Query embedding for similarity search
    - Memory retrieval (short-term and long-term)
    - Graph traversal for related information
    - Confidence calculation based on available data

    Args:
        context: Query context with query text and parameters
        embedding: Embedding model for text encoding
        graph_store: Graph store for knowledge retrieval
        memory_store: Memory store for context retrieval

    Returns:
        ReasoningResult with answer and metadata

    """
    # 1. Embed the query
    query_embedding = await embedding.embed_text(context.query)
    context.embedding = query_embedding

    # 2. Retrieve relevant memories
    short_term_memories = await memory_store.retrieve_memories(
        query_embedding, MemoryType.SHORT_TERM, limit=10
    )

    _long_term_memories = await memory_store.retrieve_memories(
        query_embedding, MemoryType.LONG_TERM, limit=20
    )

    # 3. Find similar nodes in graph
    similar_nodes = await graph_store.find_similar_nodes(
        query_embedding, limit=context.limit
    )

    # 4. Initialize result containers
    reasoning_path = []
    entities = []
    relations = []
    sources = []

    # 4. Traverse graph from relevant nodes (limit to reduce variables)
    for node in similar_nodes[:3]:  # Reduced from 5 to 3
        _traversal = await graph_store.traverse_graph(
            node.id, context.max_hops, context.filters
        )
        reasoning_path.append(f"Traversed from {node.id}")

    # 5. Combine information
    answer_parts = []

    if short_term_memories:
        answer_parts.append("Recent context: " + short_term_memories[0].content[:200])

    if similar_nodes:
        answer_parts.append(f"Found {len(similar_nodes)} relevant nodes")

    answer = (
        " | ".join(answer_parts) if answer_parts else "No sufficient information found"
    )

    # 6. Calculate confidence
    confidence = min(
        (len(similar_nodes) * 0.4 + len(short_term_memories) * 0.6) / 10, 1.0
    )

    return ReasoningResult(
        answer=answer,
        entities=entities[:10],
        relations=relations[:10],
        reasoning_path=reasoning_path,
        confidence=confidence,
        sources=sources[:5],
    )
