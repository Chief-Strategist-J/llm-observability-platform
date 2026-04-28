import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncpg
from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class AsyncPostgresDatabaseAdapter(DatabasePort):
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 50):
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool = None

    async def initialize(self):
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            command_timeout=30,
            max_inactive_connection_lifetime=300
        )
        await self._ensure_tables()

    async def _ensure_tables(self):
        async with self._pool.acquire() as conn:
            await conn.execute("SET synchronous_commit = off")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kafka_events (
                    id SERIAL PRIMARY KEY,
                    topic VARCHAR(255) NOT NULL,
                    partition INTEGER NOT NULL,
                    "offset" BIGINT NOT NULL,
                    key TEXT,
                    value JSONB,
                    timestamp TIMESTAMPTZ NOT NULL,
                    headers JSONB,
                    processed BOOLEAN DEFAULT FALSE,
                    error TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_kafka_events_unique 
                ON kafka_events(topic, partition, "offset")
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS consumer_offsets (
                    id SERIAL PRIMARY KEY,
                    consumer_group VARCHAR(255) NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    partition INTEGER NOT NULL,
                    "offset" BIGINT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(consumer_group, topic, partition)
                )
            """)

    async def save_event(self, event: EventRecord) -> str:
        async with self._pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO kafka_events 
                (topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, (
                event.topic,
                event.partition,
                event.offset,
                event.key,
                json.dumps(event.value) if event.value else None,
                event.timestamp,
                json.dumps(event.headers) if event.headers else None,
                event.processed,
                event.error,
                event.created_at
            ))
            return str(result['id'])

    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        async with self._pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO kafka_events 
                (topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT DO NOTHING
            """, [
                (e.topic, e.partition, e.offset, e.key,
                 json.dumps(e.value) if e.value else None,
                 e.timestamp,
                 json.dumps(e.headers) if e.headers else None,
                 e.processed, e.error, e.created_at)
                for e in events
            ])
        return [f"batch-{i}" for i in range(len(events))]

    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM kafka_events WHERE id = $1", event_id)
            if row:
                return self._row_to_event(row)
            return None

    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM kafka_events 
                WHERE topic = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3
            """, topic, limit, offset)
            return [self._row_to_event(row) for row in rows]

    async def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM kafka_events 
                WHERE processed = FALSE 
                ORDER BY created_at ASC 
                LIMIT $1
            """, limit)
            return [self._row_to_event(row) for row in rows]

    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE kafka_events 
                SET processed = TRUE, error = $1 
                WHERE id = $2
            """, error, event_id)
            return int(result) > 0

    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO consumer_offsets 
                (consumer_group, topic, partition, offset, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (consumer_group, topic, partition) 
                DO UPDATE SET 
                    offset = EXCLUDED.offset,
                    updated_at = EXCLUDED.updated_at
            """, (
                offset.consumer_group,
                offset.topic,
                offset.partition,
                offset.offset,
                offset.updated_at
            ))
            return True

    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM consumer_offsets 
                WHERE consumer_group = $1 AND topic = $2 AND partition = $3
            """, consumer_group, topic, partition)
            if row:
                return ConsumerOffset(
                    consumer_group=row['consumer_group'],
                    topic=row['topic'],
                    partition=row['partition'],
                    offset=row['offset'],
                    updated_at=row['updated_at']
                )
            return None

    async def delete_events_by_topic(self, topic: str) -> int:
        async with self._pool.acquire() as conn:
            result = await conn.execute("DELETE FROM kafka_events WHERE topic = $1", topic)
            return int(result)

    async def get_event_count(self, topic: Optional[str] = None) -> int:
        async with self._pool.acquire() as conn:
            if topic:
                result = await conn.fetchval("SELECT COUNT(*) FROM kafka_events WHERE topic = $1", topic)
            else:
                result = await conn.fetchval("SELECT COUNT(*) FROM kafka_events")
            return result if result else 0

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    def _row_to_event(self, row: Dict[str, Any]) -> EventRecord:
        return EventRecord(
            topic=row['topic'],
            partition=row['partition'],
            offset=row['offset'],
            key=row['key'],
            value=row['value'],
            timestamp=row['timestamp'],
            headers=row['headers'],
            processed=row['processed'],
            error=row['error'],
            created_at=row['created_at']
        )
