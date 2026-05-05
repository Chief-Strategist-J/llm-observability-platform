import json
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time
import asyncio
from collections import deque
from dataclasses import dataclass

from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset
from domain.ports.event_writer_port import EventWriterPort
from domain.ports.event_reader_port import EventReaderPort
from domain.ports.event_management_port import EventManagementPort
from domain.ports.offset_port import OffsetPort
from domain.ports.count_port import CountPort
from infrastructure.adapters.async_postgres_database_adapter import AsyncPostgresDatabaseAdapter
from infrastructure.adapters.async_mongo_database_adapter import AsyncMongoDatabaseAdapter


@dataclass
class AsyncShardingConfig:
    logical_shards_per_instance: int = 4
    batch_size: int = 100
    adaptive_batching: bool = True
    max_latency_ms: int = 50


class AsyncHorizontallyShardedDatabaseAdapter(DatabasePort, EventWriterPort, EventReaderPort, EventManagementPort, OffsetPort, CountPort):
    def __init__(self, postgres_instances: List[str], mongo_instances: List[str],
                 config: Optional[AsyncShardingConfig] = None,
                 postgres_min_size: int = 10, postgres_max_size: int = 50):
        self.config = config or AsyncShardingConfig()
        self.logical_shards_per_instance = self.config.logical_shards_per_instance
        self.total_shards = len(postgres_instances) * self.config.logical_shards_per_instance
        self.batch_size = self.config.batch_size
        self.adaptive_batching = self.config.adaptive_batching
        self.max_latency_ms = self.config.max_latency_ms
        self.current_batch_size = self.config.batch_size
        self.latency_history: deque = deque(maxlen=100)

        self.postgres_adapters = [
            AsyncPostgresDatabaseAdapter(dsn=dsn, min_size=postgres_min_size, max_size=postgres_max_size)
            for dsn in postgres_instances
        ]
        self.mongo_adapters = [
            AsyncMongoDatabaseAdapter(uri=uri, database_name="kafka_events")
            for uri in mongo_instances
        ]

        self.shard_buffers: Dict[Tuple[int, int], List[EventRecord]] = {}
        self.shard_buffer_timestamps: Dict[Tuple[int, int], float] = {}
        self.shard_healthy: Dict[Tuple[int, int], bool] = {}
        self.per_shard_buffer_limit = 10000
        self._initialized = False
        self._flusher_task: Optional[asyncio.Task] = None

        self._shard_locks: Dict[Tuple[int, int], asyncio.Lock] = {
            (instance_idx, logical_shard): asyncio.Lock()
            for instance_idx in range(len(postgres_instances))
            for logical_shard in range(self.config.logical_shards_per_instance)
        }

    async def initialize(self):
        if self._initialized:
            return

        await asyncio.gather(
            *[a.initialize() for a in self.postgres_adapters],
            *[a.initialize() for a in self.mongo_adapters]
        )
        self._initialized = True
        self._flusher_task = asyncio.create_task(self._background_flusher())

    async def _background_flusher(self):
        interval = max(0.001, self.max_latency_ms / 1000 / 2)
        while True:
            await asyncio.sleep(interval)
            for shard_key, lock in self._shard_locks.items():
                async with lock:
                    to_flush = self._extract_batch_if_due(shard_key)
                if to_flush:
                    asyncio.create_task(self._flush_shard(shard_key, to_flush))

    def _get_shard(self, key: Optional[str]) -> Tuple[int, int]:
        shard_hash = hash(key) if key else hash(str(time.time()))
        instance_idx = abs(shard_hash) % len(self.postgres_adapters)
        logical_shard = abs(shard_hash // len(self.postgres_adapters)) % self.logical_shards_per_instance
        return instance_idx, logical_shard

    def _adjust_batch_size(self, latency_ms: float):
        if not self.adaptive_batching:
            return
        self.latency_history.append(latency_ms)
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        if avg_latency > self.max_latency_ms and self.current_batch_size > 10:
            self.current_batch_size = max(10, int(self.current_batch_size * 0.8))
        elif avg_latency < self.max_latency_ms * 0.5 and self.current_batch_size < 5000:
            self.current_batch_size = min(5000, int(self.current_batch_size * 1.2))

    def _extract_batch_if_due(self, shard_key: Tuple[int, int]) -> Optional[List[EventRecord]]:
        buf = self.shard_buffers.get(shard_key)
        if not buf:
            return None
        elapsed_ms = (time.time() - self.shard_buffer_timestamps.get(shard_key, time.time())) * 1000
        if len(buf) >= self.current_batch_size or elapsed_ms >= self.max_latency_ms:
            batch = buf[:]
            self.shard_buffers[shard_key] = []
            self.shard_buffer_timestamps[shard_key] = time.time()
            return batch
        return None

    async def save_event(self, event: EventRecord) -> str:
        shard_key = self._get_shard(event.key)
        lock = self._shard_locks[shard_key]

        async with lock:
            buf = self.shard_buffers.setdefault(shard_key, [])
            self.shard_buffer_timestamps.setdefault(shard_key, time.time())
            self.shard_healthy.setdefault(shard_key, True)

            if len(buf) >= self.per_shard_buffer_limit:
                return f"buffer-full-{shard_key[0]}-{shard_key[1]}"

            buf.append(event)
            to_flush = self._extract_batch_if_due(shard_key)

        if to_flush:
            asyncio.create_task(self._flush_shard(shard_key, to_flush))

        return f"pending-{shard_key[0]}-{shard_key[1]}"

    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        shard_events: Dict[Tuple[int, int], List[EventRecord]] = {}
        for event in events:
            sk = self._get_shard(event.key)
            shard_events.setdefault(sk, []).append(event)

        flush_tasks = []
        for shard_key, event_list in shard_events.items():
            lock = self._shard_locks[shard_key]
            async with lock:
                buf = self.shard_buffers.setdefault(shard_key, [])
                self.shard_buffer_timestamps.setdefault(shard_key, time.time())
                self.shard_healthy.setdefault(shard_key, True)
                available = self.per_shard_buffer_limit - len(buf)
                buf.extend(event_list[:available])
                to_flush = self._extract_batch_if_due(shard_key)
            if to_flush:
                flush_tasks.append(asyncio.create_task(self._flush_shard(shard_key, to_flush)))

        return [f"pending-{i}" for i in range(len(events))]

    async def _flush_shard(self, shard_key: Tuple[int, int], buffer: List[EventRecord]):
        if not buffer:
            return
        instance_idx = shard_key[0]
        start_time = time.time()
        try:
            await self.postgres_adapters[instance_idx].save_events_batch(buffer)
            asyncio.create_task(self.mongo_adapters[instance_idx].save_events_batch(buffer))
            self._adjust_batch_size((time.time() - start_time) * 1000)
        except Exception:
            self.shard_healthy[shard_key] = False
            async with self._shard_locks[shard_key]:
                existing = self.shard_buffers.get(shard_key, [])
                if len(existing) + len(buffer) <= self.per_shard_buffer_limit:
                    self.shard_buffers[shard_key] = buffer[:self.batch_size] + existing
                    self.shard_buffer_timestamps[shard_key] = time.time()

    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        results = await asyncio.gather(
            *[adapter.get_event(event_id) for adapter in self.postgres_adapters],
            return_exceptions=True
        )
        for r in results:
            if r and not isinstance(r, Exception):
                return r
        return None

    async def get_events_by_topic(self, topic: str, limit: int, offset: int) -> List[EventRecord]:
        # Query all shards in parallel since events for a topic are distributed by key
        # For a full implementation, we'd need to fetch limit+offset from each and then merge/sort
        # but to keep it efficient while correct, we'll fetch 'limit + offset' from all and merge.
        results = await asyncio.gather(
            *[adapter.get_events_by_topic(topic, limit=limit + offset, offset=0) for adapter in self.postgres_adapters],
            return_exceptions=True
        )
        
        all_events = []
        for r in results:
            if not isinstance(r, Exception):
                all_events.extend(r)
        
        # Sort by created_at descending (matches AsyncPostgresDatabaseAdapter)
        all_events.sort(key=lambda x: x.created_at, reverse=True)
        
        return all_events[offset:offset + limit]

    async def get_unprocessed_events(self, limit: int) -> List[EventRecord]:
        per_shard_limit = max(1, limit // len(self.postgres_adapters))
        results = await asyncio.gather(
            *[a.get_unprocessed_events(per_shard_limit) for a in self.postgres_adapters],
            return_exceptions=True
        )
        all_events = []
        for r in results:
            if not isinstance(r, Exception):
                all_events.extend(r)
        return all_events[:limit]

    async def mark_event_processed(self, event_id: str) -> bool:
        for adapter in self.postgres_adapters:
            if await adapter.mark_event_processed(event_id):
                return True
        return False

    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        instance_idx, _ = self._get_shard(offset.consumer_group)
        return await self.postgres_adapters[instance_idx].save_consumer_offset(offset)

    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        instance_idx, _ = self._get_shard(consumer_group)
        try:
            return await self.postgres_adapters[instance_idx].get_consumer_offset(consumer_group, topic, partition)
        except Exception:
            return None

    async def delete_events_by_topic(self, topic: str) -> int:
        results = await asyncio.gather(
            *[a.delete_events_by_topic(topic) for a in self.postgres_adapters],
            return_exceptions=True
        )
        return sum(r for r in results if not isinstance(r, Exception))

    async def get_event_count(self, topic: Optional[str] = None) -> int:
        results = await asyncio.gather(
            *[a.get_event_count(topic) for a in self.postgres_adapters],
            return_exceptions=True
        )
        return sum(r for r in results if not isinstance(r, Exception))

    async def close(self):
        if self._flusher_task:
            self._flusher_task.cancel()

        for shard_key, lock in self._shard_locks.items():
            async with lock:
                buf = self.shard_buffers.get(shard_key, [])
                if buf:
                    to_flush = buf[:]
                    self.shard_buffers[shard_key] = []
                    await self._flush_shard(shard_key, to_flush)

        await asyncio.gather(
            *[a.close() for a in self.postgres_adapters],
            *[a.close() for a in self.mongo_adapters],
            return_exceptions=True
        )
