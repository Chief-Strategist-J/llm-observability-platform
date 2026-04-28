import json
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time
import asyncio
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
        self.latency_history = []

        self.postgres_adapters = []
        for i, dsn in enumerate(postgres_instances):
            adapter = AsyncPostgresDatabaseAdapter(dsn=dsn, min_size=postgres_min_size, max_size=postgres_max_size)
            self.postgres_adapters.append(adapter)

        self.mongo_adapters = []
        for i, uri in enumerate(mongo_instances):
            adapter = AsyncMongoDatabaseAdapter(uri=uri, database_name="kafka_events")
            self.mongo_adapters.append(adapter)

        self.shard_buffers: Dict[Tuple[int, int], List[EventRecord]] = {}
        self.shard_buffer_timestamps: Dict[Tuple[int, int], float] = {}
        self.shard_healthy: Dict[Tuple[int, int], bool] = {}
        self.flush_lock = asyncio.Lock()
        self.per_shard_buffer_limit = 10000
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        
        init_tasks = []
        for adapter in self.postgres_adapters:
            init_tasks.append(adapter.initialize())
        for adapter in self.mongo_adapters:
            init_tasks.append(adapter.initialize())
        
        await asyncio.gather(*init_tasks)
        self._initialized = True

    def _get_shard(self, key: Optional[str]) -> tuple:
        if key:
            shard_hash = hash(key)
        else:
            shard_hash = hash(str(time.time()))
        
        instance_idx = shard_hash % len(self.postgres_adapters)
        logical_shard = (shard_hash // len(self.postgres_adapters)) % self.logical_shards_per_instance
        return instance_idx, logical_shard
    
    def _adjust_batch_size(self, latency_ms: float):
        if not self.adaptive_batching:
            return
        
        self.latency_history.append(latency_ms)
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)
        
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        
        if avg_latency > self.max_latency_ms and self.current_batch_size > 10:
            self.current_batch_size = max(10, int(self.current_batch_size * 0.8))
        elif avg_latency < self.max_latency_ms * 0.5 and self.current_batch_size < 1000:
            self.current_batch_size = min(1000, int(self.current_batch_size * 1.2))
    
    async def save_event(self, event: EventRecord) -> str:
        instance_idx, logical_shard = self._get_shard(event.key)
        shard_key = (instance_idx, logical_shard)

        async with self.flush_lock:
            if shard_key not in self.shard_buffers:
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()
                self.shard_healthy[shard_key] = True

            if len(self.shard_buffers[shard_key]) >= self.per_shard_buffer_limit:
                return f"buffer-full-{shard_key[0]}-{shard_key[1]}"

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
            async with self.flush_lock:
                if shard_key not in self.shard_buffers:
                    self.shard_buffers[shard_key] = []
                    self.shard_buffer_timestamps[shard_key] = time.time()
                    self.shard_healthy[shard_key] = True

                if len(self.shard_buffers[shard_key]) + len(event_list) <= self.per_shard_buffer_limit:
                    self.shard_buffers[shard_key].extend(event_list)
                    results.extend([f"pending-{shard_key[0]}-{shard_key[1]}-{i}" for i in range(len(event_list))])
                else:
                    results.extend([f"buffer-full-{shard_key[0]}-{shard_key[1]}" for _ in event_list])

            await self._check_and_flush_shard(shard_key)

        return results

    async def _check_and_flush_shard(self, shard_key: Tuple[int, int]):
        async with self.flush_lock:
            buffer = self.shard_buffers.get(shard_key, [])
            buffer_size = len(buffer)
            elapsed_ms = (time.time() - self.shard_buffer_timestamps.get(shard_key, time.time())) * 1000

            should_flush = (
                buffer_size >= self.batch_size or
                elapsed_ms >= self.max_latency_ms
            )

            if should_flush and buffer_size > 0 and self.shard_healthy.get(shard_key, True):
                to_flush = buffer[:]
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()
                await self._flush_shard(shard_key, to_flush)

    async def _flush_shard(self, shard_key: Tuple[int, int], buffer: List[EventRecord]):
        if not buffer:
            return

        instance_idx, logical_shard = shard_key
        start_time = time.time()

        try:
            postgres_adapter = self.postgres_adapters[instance_idx]
            await postgres_adapter.save_events_batch(buffer)

            mongo_adapter = self.mongo_adapters[instance_idx]
            await mongo_adapter.save_events_batch(buffer)

            flush_duration_ms = (time.time() - start_time) * 1000
            self._adjust_batch_size(flush_duration_ms)

        except Exception as e:
            self.shard_healthy[shard_key] = False
            async with self.flush_lock:
                if len(buffer) > self.batch_size:
                    self.shard_buffers[shard_key] = buffer[:self.batch_size]
                    self.shard_buffer_timestamps[shard_key] = time.time()
    
    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        for adapter in self.postgres_adapters:
            try:
                event = await adapter.get_event(event_id)
                if event:
                    return event
            except Exception:
                continue
        return None
    
    async def get_events_by_topic(self, topic: str, limit: int, offset: int) -> List[EventRecord]:
        return await self.postgres_adapters[0].get_events_by_topic(topic, limit, offset)
    
    async def get_unprocessed_events(self, limit: int) -> List[EventRecord]:
        all_events = []
        per_shard_limit = max(1, limit // len(self.postgres_adapters))
        tasks = [adapter.get_unprocessed_events(per_shard_limit) for adapter in self.postgres_adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                continue
            all_events.extend(result)
        return all_events[:limit]
    
    async def mark_event_processed(self, event_id: str) -> bool:
        for adapter in self.postgres_adapters:
            if await adapter.mark_event_processed(event_id):
                return True
        return False
    
    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        instance_idx, _ = self._get_shard(offset.consumer_group)
        return await self.postgres_adapters[instance_idx].save_consumer_offset(offset)
    
    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        instance_idx, _ = self._get_shard(consumer_group)
        try:
            return await self.postgres_adapters[instance_idx].get_consumer_offset(consumer_group, topic, partition)
        except Exception:
            return None
    
    async def delete_events_by_topic(self, topic: str) -> int:
        tasks = [adapter.delete_events_by_topic(topic) for adapter in self.postgres_adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total = 0
        for result in results:
            if isinstance(result, Exception):
                continue
            total += result
        return total
    
    async def get_event_count(self, topic: str) -> int:
        tasks = [adapter.get_event_count(topic) for adapter in self.postgres_adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total = 0
        for result in results:
            if isinstance(result, Exception):
                continue
            total += result
        return total
    
    async def close(self):
        async with self.flush_lock:
            for shard_key in list(self.shard_buffers.keys()):
                buffer = self.shard_buffers.get(shard_key, [])
                if buffer:
                    to_flush = buffer[:]
                    self.shard_buffers[shard_key] = []
                    await self._flush_shard(shard_key, to_flush)

        tasks = []
        for adapter in self.postgres_adapters:
            tasks.append(adapter.close())
        for adapter in self.mongo_adapters:
            tasks.append(adapter.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
