"""Memory management use cases for knowledge graph service.

This module contains functions for storing interactions and managing memory decay.

"""

from datetime import datetime

from ..domain.models import Memory, MemoryType
from ..ports.embedding_model import EmbeddingModelPort
from ..ports.memory_store import MemoryStorePort


async def store_interaction(
    query: str,
    response: str,
    memory_store: MemoryStorePort,
    embedding: EmbeddingModelPort,
) -> str:
    """Store a query-response interaction in memory.

    Args:
        query: The user's query
        response: The system's response
        memory_store: Memory storage interface
        embedding: Embedding model for content encoding

    Returns:
        Memory ID of the stored interaction

    """
    content = f"Q: {query}\nA: {response}"
    embedding_vec = await embedding.embed_text(content)

    memory = Memory(
        id=f"mem_{datetime.utcnow().timestamp()}",
        content=content,
        memory_type=MemoryType.SHORT_TERM,
        importance=0.5,
        created_at=datetime.utcnow(),
        accessed_at=datetime.utcnow(),
        embedding=embedding_vec,
    )

    return await memory_store.store_memory(memory)


async def decay_old_memories(memory_store: MemoryStorePort) -> int:
    """Decay old memories to maintain memory store efficiency.

    Args:
        memory_store: Memory storage interface

    Returns:
        Number of memories decayed

    """
    return await memory_store.decay_memories()
