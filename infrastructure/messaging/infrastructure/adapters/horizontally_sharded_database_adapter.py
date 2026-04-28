import json
import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time
import threading
import asyncio
import concurrent.futures
from dataclasses import dataclass
import psycopg2
from psycopg2 import pool, extras
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset
from domain.ports.event_writer_port import EventWriterPort
from domain.ports.event_reader_port import EventReaderPort
from domain.ports.event_management_port import EventManagementPort
from domain.ports.offset_port import OffsetPort
from domain.ports.count_port import CountPort
from infrastructure.adapters.postgres_database_adapter import PostgresDatabaseAdapter
from infrastructure.adapters.mongodb_database_adapter import MongoDatabaseAdapter


@dataclass
class ShardingConfig:
    logical_shards_per_instance: int = 4
    batch_size: int = 100
    adaptive_batching: bool = True
    max_latency_ms: int = 50


class HorizontallyShardedDatabaseAdapter(DatabasePort, EventWriterPort, EventReaderPort, EventManagementPort, OffsetPort, CountPort):
    def __init__(self, postgres_instances: List[str], mongo_instances: List[str],
                 config: Optional[ShardingConfig] = None, thread_pool_workers: int = 200,
                 postgres_minconn: int = 10, postgres_maxconn: int = 50):
        self.config = config or ShardingConfig()
        self.logical_shards_per_instance = self.config.logical_shards_per_instance
        self.total_shards = len(postgres_instances) * self.config.logical_shards_per_instance
        self.batch_size = self.config.batch_size
        self.adaptive_batching = self.config.adaptive_batching
        self.max_latency_ms = self.config.max_latency_ms
        self.current_batch_size = self.config.batch_size
        self.latency_history = []

        self.postgres_adapters = []
        for i, dsn in enumerate(postgres_instances):
            adapter = PostgresDatabaseAdapter(dsn=dsn, minconn=postgres_minconn, maxconn=postgres_maxconn)
            self.postgres_adapters.append(adapter)

        self.mongo_adapters = []
        for i, uri in enumerate(mongo_instances):
            adapter = MongoDatabaseAdapter(uri=uri, database_name="kafka_events")
            self.mongo_adapters.append(adapter)

        self.shard_buffers: Dict[Tuple[int, int], List[EventRecord]] = {}
        self.shard_buffer_timestamps: Dict[Tuple[int, int], float] = {}
        self.shard_healthy: Dict[Tuple[int, int], bool] = {}
        self.flush_lock = threading.Lock()
        self.per_shard_buffer_limit = 10000
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=thread_pool_workers)
    
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
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_save_event, event
        )

    def _sync_save_event(self, event: EventRecord) -> str:
        instance_idx, logical_shard = self._get_shard(event.key)
        shard_key = (instance_idx, logical_shard)

        with self.flush_lock:
            if shard_key not in self.shard_buffers:
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()
                self.shard_healthy[shard_key] = True

            if len(self.shard_buffers[shard_key]) >= self.per_shard_buffer_limit:
                return f"buffer-full-{shard_key[0]}-{shard_key[1]}"

            self.shard_buffers[shard_key].append(event)

        self._check_and_flush_shard(shard_key)
        return f"pending-{shard_key[0]}-{shard_key[1]}-{len(self.shard_buffers[shard_key])}"
    
    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_save_events_batch, events
        )

    def _sync_save_events_batch(self, events: List[EventRecord]) -> List[str]:
        shard_events: Dict[Tuple[int, int], List[EventRecord]] = {}
        for event in events:
            shard_key = self._get_shard(event.key)
            if shard_key not in shard_events:
                shard_events[shard_key] = []
            shard_events[shard_key].append(event)

        results = []
        for shard_key, event_list in shard_events.items():
            with self.flush_lock:
                if shard_key not in self.shard_buffers:
                    self.shard_buffers[shard_key] = []
                    self.shard_buffer_timestamps[shard_key] = time.time()
                    self.shard_healthy[shard_key] = True

                if len(self.shard_buffers[shard_key]) + len(event_list) <= self.per_shard_buffer_limit:
                    self.shard_buffers[shard_key].extend(event_list)
                    results.extend([f"pending-{shard_key[0]}-{shard_key[1]}-{i}" for i in range(len(event_list))])
                else:
                    results.extend([f"buffer-full-{shard_key[0]}-{shard_key[1]}" for _ in event_list])

            self._check_and_flush_shard(shard_key)

        return results

    def _check_and_flush_shard(self, shard_key: Tuple[int, int]):
        buffer = self.shard_buffers.get(shard_key, [])
        buffer_size = len(buffer)
        elapsed_ms = (time.time() - self.shard_buffer_timestamps.get(shard_key, time.time())) * 1000

        should_flush = (
            buffer_size >= self.batch_size or
            elapsed_ms >= self.max_latency_ms
        )

        if should_flush and buffer_size > 0 and self.shard_healthy.get(shard_key, True):
            self._flush_shard(shard_key)

    def _flush_shard(self, shard_key: Tuple[int, int]):
        with self.flush_lock:
            buffer = self.shard_buffers.get(shard_key, [])
            if not buffer:
                return

            instance_idx, logical_shard = shard_key
            start_time = time.time()

            try:
                postgres_adapter = self.postgres_adapters[instance_idx]
                postgres_adapter.save_events_batch(buffer)

                mongo_adapter = self.mongo_adapters[instance_idx]
                mongo_adapter.save_events_batch(buffer)

                flush_duration_ms = (time.time() - start_time) * 1000
                self.shard_buffers[shard_key] = []
                self.shard_buffer_timestamps[shard_key] = time.time()

                self._adjust_batch_size(flush_duration_ms)

            except Exception as e:
                self.shard_healthy[shard_key] = False
                if len(buffer) > self.batch_size:
                    self.shard_buffers[shard_key] = buffer[:self.batch_size]
                    self.shard_buffer_timestamps[shard_key] = time.time()
    
    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_get_event, event_id
        )

    def _sync_get_event(self, event_id: str) -> Optional[EventRecord]:
        for adapter in self.postgres_adapters:
            try:
                event = adapter.get_event(event_id)
                if event:
                    return event
            except Exception:
                continue
        return None
    
    async def get_events_by_topic(self, topic: str, limit: int, offset: int) -> List[EventRecord]:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_get_events_by_topic, topic, limit, offset
        )

    def _sync_get_events_by_topic(self, topic: str, limit: int, offset: int) -> List[EventRecord]:
        return self.postgres_adapters[0].get_events_by_topic(topic, limit, offset)
    
    async def get_unprocessed_events(self, limit: int) -> List[EventRecord]:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_get_unprocessed_events, limit
        )

    def _sync_get_unprocessed_events(self, limit: int) -> List[EventRecord]:
        all_events = []
        per_shard_limit = max(1, limit // len(self.postgres_adapters))
        for adapter in self.postgres_adapters:
            all_events.extend(adapter.get_unprocessed_events(per_shard_limit))
        return all_events[:limit]
    
    async def mark_event_processed(self, event_id: str) -> bool:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_mark_event_processed, event_id
        )

    def _sync_mark_event_processed(self, event_id: str) -> bool:
        for adapter in self.postgres_adapters:
            if adapter.mark_event_processed(event_id):
                return True
        return False
    
    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_save_consumer_offset, offset
        )

    def _sync_save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        instance_idx, _ = self._get_shard(offset.consumer_group)
        return self.postgres_adapters[instance_idx].save_consumer_offset(offset)
    
    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_get_consumer_offset, consumer_group, topic, partition
        )

    def _sync_get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        instance_idx, _ = self._get_shard(consumer_group)
        try:
            return self.postgres_adapters[instance_idx].get_consumer_offset(consumer_group, topic, partition)
        except Exception:
            return None
    
    async def delete_events_by_topic(self, topic: str) -> int:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_delete_events_by_topic, topic
        )

    def _sync_delete_events_by_topic(self, topic: str) -> int:
        total = 0
        for adapter in self.postgres_adapters:
            total += adapter.delete_events_by_topic(topic)
        return total
    
    async def get_event_count(self, topic: str) -> int:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._sync_get_event_count, topic
        )

    def _sync_get_event_count(self, topic: str) -> int:
        total = 0
        for adapter in self.postgres_adapters:
            total += adapter.get_event_count(topic)
        return total
    
    def close(self):
        for shard_key in list(self.shard_buffers.keys()):
            self._flush_shard(shard_key)

        for adapter in self.postgres_adapters:
            adapter.close()
        for adapter in self.mongo_adapters:
            adapter.close()
        self._executor.shutdown(wait=True)
