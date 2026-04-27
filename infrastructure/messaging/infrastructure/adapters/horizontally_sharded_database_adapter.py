import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import psycopg2
from psycopg2 import pool, extras
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset
from infrastructure.adapters.postgres_database_adapter import PostgresDatabaseAdapter
from infrastructure.adapters.mongodb_database_adapter import MongoDatabaseAdapter


class HorizontallyShardedDatabaseAdapter(DatabasePort):
    def __init__(self, postgres_instances: List[str], mongo_instances: List[str], 
                 logical_shards_per_instance: int = 4, batch_size: int = 100,
                 adaptive_batching: bool = True, max_latency_ms: int = 50):
        self.logical_shards_per_instance = logical_shards_per_instance
        self.total_shards = len(postgres_instances) * logical_shards_per_instance
        self.batch_size = batch_size
        self.adaptive_batching = adaptive_batching
        self.max_latency_ms = max_latency_ms
        self.current_batch_size = batch_size
        self.latency_history = []
        
        self.postgres_adapters = []
        for i, dsn in enumerate(postgres_instances):
            adapter = PostgresDatabaseAdapter(dsn=dsn, minconn=2, maxconn=10)
            self.postgres_adapters.append(adapter)
        
        self.mongo_adapters = []
        for i, uri in enumerate(mongo_instances):
            adapter = MongoDatabaseAdapter(uri=uri, database_name="kafka_events")
            self.mongo_adapters.append(adapter)
    
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
    
    def save_event(self, event: EventRecord) -> str:
        instance_idx, logical_shard = self._get_shard(event.key)
        postgres_adapter = self.postgres_adapters[instance_idx]
        
        postgres_id = postgres_adapter.save_event(event)
        
        return postgres_id
    
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        start_time = time.time()
        
        shard_events = {}
        for event in events:
            instance_idx, logical_shard = self._get_shard(event.key)
            key = (instance_idx, logical_shard)
            if key not in shard_events:
                shard_events[key] = []
            shard_events[key].append(event)
        
        results = []
        for (instance_idx, logical_shard), event_list in shard_events.items():
            postgres_results = self.postgres_adapters[instance_idx].save_events_batch(event_list)
            results.extend(postgres_results)
        
        latency_ms = (time.time() - start_time) * 1000
        self._adjust_batch_size(latency_ms)
        return results
    
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        for adapter in self.postgres_adapters:
            try:
                event = adapter.get_event(event_id)
                if event:
                    return event
            except Exception:
                continue
        return None
    
    def get_events_by_topic(self, topic: str, limit: int, offset: int) -> List[EventRecord]:
        return self.postgres_adapters[0].get_events_by_topic(topic, limit, offset)
    
    def get_unprocessed_events(self, limit: int) -> List[EventRecord]:
        all_events = []
        per_shard_limit = max(1, limit // len(self.postgres_adapters))
        for adapter in self.postgres_adapters:
            all_events.extend(adapter.get_unprocessed_events(per_shard_limit))
        return all_events[:limit]
    
    def mark_event_processed(self, event_id: str) -> bool:
        for adapter in self.postgres_adapters:
            if adapter.mark_event_processed(event_id):
                return True
        return False
    
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        instance_idx, _ = self._get_shard(offset.consumer_group)
        return self.postgres_adapters[instance_idx].save_consumer_offset(offset)
    
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        instance_idx, _ = self._get_shard(consumer_group)
        try:
            return self.postgres_adapters[instance_idx].get_consumer_offset(consumer_group, topic, partition)
        except Exception:
            return None
    
    def delete_events_by_topic(self, topic: str) -> int:
        total = 0
        for adapter in self.postgres_adapters:
            total += adapter.delete_events_by_topic(topic)
        return total
    
    def get_event_count(self, topic: str) -> int:
        total = 0
        for adapter in self.postgres_adapters:
            total += adapter.get_event_count(topic)
        return total
    
    def close(self):
        for adapter in self.postgres_adapters:
            adapter.close()
        for adapter in self.mongo_adapters:
            adapter.close()
