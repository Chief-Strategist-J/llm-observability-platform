from datetime import datetime
from core.domain.models import Memory, MemoryType
from core.ports.memory_store import MemoryStorePort
from core.ports.embedding_model import EmbeddingModelPort

async def store_interaction(
    query: str,
    response: str,
    memory_store: MemoryStorePort,
    embedding: EmbeddingModelPort
) -> str:
    content = f"Q: {query}\nA: {response}"
    embedding_vec = await embedding.embed_text(content)
    
    memory = Memory(
        id=f"mem_{datetime.utcnow().timestamp()}",
        content=content,
        memory_type=MemoryType.SHORT_TERM,
        importance=0.5,
        created_at=datetime.utcnow(),
        accessed_at=datetime.utcnow(),
        embedding=embedding_vec
    )
    
    return await memory_store.store_memory(memory)

async def decay_old_memories(memory_store: MemoryStorePort) -> int:
    return await memory_store.decay_memories()
