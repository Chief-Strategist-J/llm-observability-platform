from neo4j import AsyncGraphDatabase
from typing import List
from datetime import datetime, timedelta
import os
from core.ports.memory_store import MemoryStorePort
from core.domain.models import Memory, MemoryType

class Neo4jMemoryStore(MemoryStorePort):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.decay_days = int(os.getenv("LONG_TERM_MEMORY_DECAY_DAYS", 30))
    
    async def store_memory(self, memory: Memory) -> str:
        async with self.driver.session() as session:
            query = """
            CREATE (m:Memory {
                id: $id,
                content: $content,
                memory_type: $memory_type,
                importance: $importance,
                created_at: $created_at,
                accessed_at: $accessed_at,
                access_count: $access_count,
                embedding: $embedding
            })
            RETURN m.id as id
            """
            result = await session.run(
                query,
                id=memory.id,
                content=memory.content,
                memory_type=memory.memory_type.value,
                importance=memory.importance,
                created_at=memory.created_at.isoformat(),
                accessed_at=memory.accessed_at.isoformat(),
                access_count=memory.access_count,
                embedding=memory.embedding
            )
            record = await result.single()
            return record["id"] if record else memory.id
    
    async def retrieve_memories(self, query_embedding: List[float], memory_type: MemoryType, limit: int) -> List[Memory]:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {memory_type: $memory_type})
            WHERE m.embedding IS NOT NULL
            RETURN m
            ORDER BY m.importance DESC
            LIMIT $limit
            """
            result = await session.run(
                query,
                memory_type=memory_type.value,
                limit=limit
            )
            
            memories = []
            async for record in result:
                mem_data = dict(record["m"])
                memory = Memory(
                    id=mem_data["id"],
                    content=mem_data["content"],
                    memory_type=MemoryType(mem_data["memory_type"]),
                    importance=mem_data["importance"],
                    created_at=datetime.fromisoformat(mem_data["created_at"]),
                    accessed_at=datetime.fromisoformat(mem_data["accessed_at"]),
                    access_count=mem_data["access_count"],
                    embedding=mem_data.get("embedding")
                )
                memories.append(memory)
            return memories
    
    async def update_memory_access(self, memory_id: str) -> bool:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {id: $memory_id})
            SET m.accessed_at = $now,
                m.access_count = m.access_count + 1
            RETURN m
            """
            result = await session.run(
                query,
                memory_id=memory_id,
                now=datetime.utcnow().isoformat()
            )
            return await result.single() is not None
    
    async def decay_memories(self) -> int:
        async with self.driver.session() as session:
            decay_date = (datetime.utcnow() - timedelta(days=self.decay_days)).isoformat()
            query = """
            MATCH (m:Memory {memory_type: $long_term})
            WHERE m.created_at < $decay_date AND m.importance < 0.7
            DELETE m
            RETURN count(m) as deleted_count
            """
            result = await session.run(
                query,
                long_term=MemoryType.LONG_TERM.value,
                decay_date=decay_date
            )
            record = await result.single()
            return record["deleted_count"] if record else 0
    
    async def close(self):
        await self.driver.close()
