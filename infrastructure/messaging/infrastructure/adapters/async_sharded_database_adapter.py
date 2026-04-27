import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

import asyncpg
import motor.motor_asyncio
from aiokafka import AIOKafkaProducer

from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


@dataclass
class PoolConfig:
    min_size: int = 2
    max_size: int = 20
    timeout: float = 5.0


@dataclass
class FlushConfig:
    batch_size: int = 1000
    flush_timeout_ms: int = 20
    max_batch_size: int = 5000
    max_flush_timeout_ms: int = 50


class AsyncShardedDatabaseAdapter(DatabasePort):
    def __init__(self, postgres_instances: List[str], mongo_instances: List[str],
                 logical_shards_per_instance: int = 4, pool_config: Optional[PoolConfig] = None,
                 flush_config: Optional[FlushConfig] = None, kafka_bootstrap_servers: Optional[str] = None):
        self.logical_shards_per_instance = logical_shards_per_instance
        self.total_shards = len(postgres_instances) * logical_shards_per_instance
        self.pool_config = pool_config or PoolConfig()
        self.flush_config = flush_config or FlushConfig()
        self.kafka_bootstrap_servers = kafka_bootstrap_servers

        self.postgres_pools = []
        self.mongo_clients = []
        self.kafka_producer = None

        self.shard_buffers: Dict[Tuple[int, int], List[EventRecord]] = {}
        self.shard_buffer_timestamps: Dict[Tuple[int, int], float] = {}
        self.shard_healthy: Dict[Tuple[int, int], bool] = {}
        self.flush_lock = asyncio.Lock()

        self._init_postgres(postgres_instances)
        self._init_mongo(mongo_instances)
        if kafka_bootstrap_servers:
            self._init_kafka(kafka_bootstrap_servers)

    def _init_postgres(self, instances: List[str]):
        for dsn in instances:
            self.postgres_pools.append(None)

    def _init_mongo(self, instances: List[str]):
        for uri in instances:
            self.mongo_clients.append(None)

    def _init_kafka(self, bootstrap_servers: str):
        self.kafka_producer = None

    async def _get_postgres_pool(self, instance_idx: int) -> asyncpg.Pool:
        if self.postgres_pools[instance_idx] is None:
            dsn = self._get_postgres_dsn(instance_idx)
            self.postgres_pools[instance_idx] = await asyncpg.create_pool(
                dsn,
                min_size=self.pool_config.min_size,
                max_size=self.pool_config.max_size,
                command_timeout=self.pool_config.timeout
            )
        return self.postgres_pools[instance_idx]

    async def _get_mongo_client(self, instance_idx: int) -> motor.motor_asyncio.AsyncIOMotorClient:
        if self.mongo_clients[instance_idx] is None:
            uri = self._get_mongo_uri(instance_idx)
            self.mongo_clients[instance_idx] = motor.motor_asyncio.AsyncIOMotorClient(uri)
        return self.mongo_clients[instance_idx]

    def _get_postgres_dsn(self, instance_idx: int) -> str:
        return f"postgresql://postgres:postgres@messaging-postgres-{instance_idx}:5432/messaging"

    def _get_mongo_uri(self, instance_idx: int) -> str:
        return f"mongodb://admin:admin@messaging-mongodb-{instance_idx}:27017/"

    def _get_shard(self, key: Optional[str]) -> Tuple[int, int]:
        if key:
            shard_hash = hash(key)
        else:
            shard_hash = hash(str(time.time()))

        instance_idx = shard_hash % len(self.postgres_pools)
        logical_shard = (shard_hash // len(self.postgres_pools)) % self.logical_shards_per_instance
        return instance_idx, logical_shard

    async def save_event(self, event: EventRecord) -> str:
        instance_idx, logical_shard = self._get_shard(event.key)
        shard_key = (instance_idx, logical_shard)

        if shard_key not in self.shard_buffers:
            self.shard_buffers[shard_key] = []
            self.shard_buffer_timestamps[shard_key] = time.time()
            self.shard_healthy[shard_key] = True

        self.shard_buffers[shard_key].append(event)

        await self._check_and_flush_shard(shard_key)
        return f"pending-{shard_key[0]}-{shard_key[1]}-{len(self.shard_buffers[shard_key])}"

    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        shard_events: Dict[Tuple[int, int], List[EventRecord]] = {}
        for event in events:
            shard_key = self._get_shard(event.key)
            if shard_key not in shard_events:
                shard_events[shard_key] = []
            shard_events[shard_key].append(event)

        results = []
        for shard_key, event_list in shard_events.items():
            if shard_key not in self.shard_buffers:
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()
                self.shard_healthy[shard_key] = True

            self.shard_buffers[shard_key].extend(event_list)
            await self._check_and_flush_shard(shard_key)
            results.extend([f"pending-{shard_key[0]}-{shard_key[1]}-{i}" for i in range(len(event_list))])

        return results

    async def _check_and_flush_shard(self, shard_key: Tuple[int, int]):
        buffer = self.shard_buffers[shard_key]
        buffer_size = len(buffer)
        elapsed_ms = (time.time() - self.shard_buffer_timestamps[shard_key]) * 1000

        should_flush = (
            buffer_size >= self.flush_config.batch_size or
            elapsed_ms >= self.flush_config.flush_timeout_ms
        )

        if should_flush and buffer_size > 0 and self.shard_healthy[shard_key]:
            await self._flush_shard(shard_key)

    async def _flush_shard(self, shard_key: Tuple[int, int]):
        async with self.flush_lock:
            buffer = self.shard_buffers[shard_key]
            if not buffer:
                return

            instance_idx, logical_shard = shard_key
            start_time = time.time()

            try:
                postgres_pool = await self._get_postgres_pool(instance_idx)
                await self._flush_to_postgres(postgres_pool, buffer)

                mongo_client = await self._get_mongo_client(instance_idx)
                await self._flush_to_mongo(mongo_client, buffer)

                if self.kafka_producer:
                    await self._flush_to_kafka(buffer)

                flush_duration_ms = (time.time() - start_time) * 1000
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()

            except Exception as e:
                self.shard_healthy[shard_key] = False
                if len(buffer) > self.flush_config.max_batch_size:
                    self.shard_buffers[shard_key] = buffer[:self.flush_config.max_batch_size]
                    self.shard_buffer_timestamps[shard_key] = time.time()

    async def _flush_to_postgres(self, pool: asyncpg.Pool, events: List[EventRecord]):
        async with pool.acquire() as conn:
            async with conn.transaction():
                for event in events:
                    await conn.execute("""
                        INSERT INTO kafka_events 
                        (topic, partition, "offset", key, value, timestamp, headers, processed, error, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
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

    async def _flush_to_mongo(self, client: motor.motor_asyncio.AsyncIOMotorClient, events: List[EventRecord]):
        db = client["kafka_events"]
        collection = db["kafka_events"]

        docs = []
        for event in events:
            docs.append({
                "topic": event.topic,
                "partition": event.partition,
                "offset": event.offset,
                "key": event.key,
                "value": event.value,
                "timestamp": event.timestamp,
                "headers": event.headers,
                "processed": event.processed,
                "error": event.error,
                "created_at": event.created_at
            })

        if docs:
            await collection.insert_many(docs)

    async def _flush_to_kafka(self, events: List[EventRecord]):
        pass

    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        for i, pool in enumerate(self.postgres_pools):
            if pool is None:
                continue
            try:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM kafka_events WHERE id = $1", event_id)
                    if row:
                        return self._row_to_event(row)
            except Exception:
                continue
        return None

    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        if not self.postgres_pools or self.postgres_pools[0] is None:
            return []
        pool = self.postgres_pools[0]
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM kafka_events 
                WHERE topic = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3
            """, topic, limit, offset)
            return [self._row_to_event(row) for row in rows]

    async def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        all_events = []
        per_shard_limit = max(1, limit // len(self.postgres_pools))
        for pool in self.postgres_pools:
            if pool is None:
                continue
            try:
                async with pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT * FROM kafka_events 
                        WHERE processed = FALSE 
                        ORDER BY created_at ASC 
                        LIMIT $1
                    """, per_shard_limit)
                    all_events.extend([self._row_to_event(row) for row in rows])
            except Exception:
                continue
        return all_events[:limit]

    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        for pool in self.postgres_pools:
            if pool is None:
                continue
            try:
                async with pool.acquire() as conn:
                    result = await conn.execute("""
                        UPDATE kafka_events 
                        SET processed = TRUE, error = $1 
                        WHERE id = $2
                    """, error, event_id)
                    if result == "UPDATE 1":
                        return True
            except Exception:
                continue
        return False

    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        instance_idx, _ = self._get_shard(offset.consumer_group)
        pool = await self._get_postgres_pool(instance_idx)
        async with pool.acquire() as conn:
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
        instance_idx, _ = self._get_shard(consumer_group)
        pool = await self._get_postgres_pool(instance_idx)
        async with pool.acquire() as conn:
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
        total = 0
        for pool in self.postgres_pools:
            if pool is None:
                continue
            try:
                async with pool.acquire() as conn:
                    result = await conn.execute("DELETE FROM kafka_events WHERE topic = $1", topic)
                    total += int(result.split()[-1])
            except Exception:
                continue
        return total

    async def get_event_count(self, topic: Optional[str] = None) -> int:
        total = 0
        for pool in self.postgres_pools:
            if pool is None:
                continue
            try:
                async with pool.acquire() as conn:
                    if topic:
                        result = await conn.fetchval("SELECT COUNT(*) FROM kafka_events WHERE topic = $1", topic)
                    else:
                        result = await conn.fetchval("SELECT COUNT(*) FROM kafka_events")
                    total += result
            except Exception:
                continue
        return total

    async def close(self) -> None:
        for shard_key in list(self.shard_buffers.keys()):
            await self._flush_shard(shard_key)

        for pool in self.postgres_pools:
            if pool:
                await pool.close()

        for client in self.mongo_clients:
            if client:
                client.close()

        if self.kafka_producer:
            await self.kafka_producer.stop()

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
