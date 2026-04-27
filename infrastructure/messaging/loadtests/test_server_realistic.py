from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import os
import sys

from application.api.v1.database_api import DatabaseAPI
from application.api.v1.schema_registry_api import SchemaRegistryAPI
from application.api.v1.event_handler_api import EventHandlerAPI, SchemaAwareEventHandlerAPI
from application.api.v1.producer_api import ProducerAPI
from application.api.v1.consumer_api import ConsumerAPI
from application.api.v1.broker_api import BrokerAPI
from domain.ports.database_port import EventRecord, ConsumerOffset, DatabasePort
from domain.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo
from domain.ports.producer_port import ProducerPort, ProduceMessageParams, TopicCreationParams
from domain.ports.consumer_port import ConsumerPort, ConsumeParams, ParallelConsumeParams, ConsumerOffsetParams
from domain.ports.broker_port import BrokerPort
from domain.services.event_handler import EventHandler
from domain.services.schema_aware_event_handler import SchemaAwareEventHandler
from infrastructure.adapters.horizontally_sharded_database_adapter import HorizontallyShardedDatabaseAdapter, ShardingConfig
from infrastructure.queue.in_memory_queue import InMemoryQueue, QueueConfig
from infrastructure.adapters.redis_idempotency_store import RedisIdempotencyStore
from infrastructure.metrics.metrics_collector import MetricsCollector
from application.api.v1.database_api import DatabaseAPIConfig
from application.middleware.logging_middleware import LoggingMiddleware
from application.middleware.auth_middleware import AuthMiddleware
from application.middleware.sanitization_middleware import SanitizationMiddleware


class MockSchemaRegistry(SchemaRegistryPort):
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        return 1
    
    def get_schema(self, schema_id: int) -> SchemaInfo:
        return SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
    
    def get_schema_by_subject(self, subject: str, version: int = None) -> SchemaInfo:
        return SchemaInfo(
            subject=subject,
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
    
    def get_latest_schema(self, subject: str) -> SchemaInfo:
        return SchemaInfo(
            subject=subject,
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
    
    def list_subjects(self) -> List[str]:
        return ["subject1", "subject2"]
    
    def list_versions(self, subject: str) -> List[int]:
        return [1, 2, 3]
    
    def delete_subject(self, subject: str) -> bool:
        return True
    
    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        return True
    
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        return True
    
    def serialize(self, subject: str, data: Dict, schema_id: int = None) -> bytes:
        return b"serialized-data"
    
    def deserialize(self, data: bytes, schema_id: int) -> Dict:
        return {"key": "value"}
    
    def close(self):
        pass


class MockProducer(ProducerPort):
    def produce(self, params: ProduceMessageParams) -> Dict[str, Any]:
        return {
            "topic": params.topic,
            "partition": params.partition or 0,
            "offset": 0,
            "key": params.key,
            "timestamp": 0
        }

    def produce_async(self, params: ProduceMessageParams) -> asyncio.Future:
        future = asyncio.Future()
        future.set_result({
            "topic": params.topic,
            "partition": params.partition or 0,
            "offset": 0,
            "key": params.key,
            "timestamp": 0
        })
        return future

    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"topic": topic, "partition": 0, "offset": 100 + i, "timestamp": 1234567890} for i in range(len(messages))]
    
    def flush(self, timeout: float = 10.0) -> None:
        pass
    
    def list_topics(self) -> List[str]:
        return ["topic1", "topic2"]
    
    def create_topic(self, params: TopicCreationParams) -> bool:
        return True


class MockConsumer(ConsumerPort):
    def consume(self, params: ConsumeParams) -> List[Dict[str, Any]]:
        return []

    def consume_parallel(self, params: ParallelConsumeParams) -> Dict[int, List[Dict[str, Any]]]:
        return {p: [{"topic": params.topic, "partition": p, "offset": 100, "key": "key", "value": "value", "timestamp": 1234567890, "headers": {}} for _ in range(params.max_messages_per_partition)] for p in params.partitions}

    def consume_stream(self, topic: str, consumer_group: str, message_handler, batch_size: int = 100) -> None:
        pass

    def stop_stream(self) -> None:
        pass

    def commit_offset(self, params: ConsumerOffsetParams) -> bool:
        return True

    def commit_offsets_batch(self, offsets: Dict[str, Dict[int, int]]) -> bool:
        return True

    def get_offset(self, consumer_group: str, topic: str, partition: int) -> int:
        return 100

    def subscribe(self, topic: str, consumer_group: str) -> bool:
        return True
    
    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        return True
    
    def list_subscriptions(self, consumer_group: str) -> List[str]:
        return ["topic1", "topic2"]


class MockBroker(BrokerPort):
    def get_broker_metadata(self) -> Dict:
        return {"cluster_id": "test-cluster", "controller_id": 1, "broker_count": 3, "topic_count": 10}
    
    def list_brokers(self) -> List:
        return [{"broker_id": 1, "host": "localhost", "port": 9092, "rack": "rack1"}]
    
    def get_broker_info(self, broker_id: int) -> Dict:
        return {"broker_id": broker_id, "host": "localhost", "port": 9092, "rack": "rack1"}
    
    def list_topics(self) -> List:
        return ["topic1", "topic2", "topic3"]
    
    def get_topic_metadata(self, topic_name: str) -> Dict:
        return {"topic_name": topic_name, "partition_count": 3, "replication_factor": 2, "partitions": []}
    
    def get_consumer_groups(self) -> List:
        return [{"group_id": "group1", "state": "Stable", "members": 3, "topics": ["topic1"]}]
    
    def get_consumer_group_lag(self, group_id: str) -> List:
        return [{"group_id": group_id, "topic": "topic1", "partition": 0, "current_offset": 100, "log_end_offset": 150, "lag": 50}]
    
    def get_cluster_config(self) -> Dict:
        return {"num.partitions": "3", "default.replication.factor": "2"}


app = FastAPI(title="Messaging API Realistic Test Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

postgres_instances = [
    "postgresql://postgres:postgres@postgres:5432/messaging",
    "postgresql://postgres:postgres@postgres-1:5432/messaging",
    "postgresql://postgres:postgres@postgres-2:5432/messaging",
    "postgresql://postgres:postgres@postgres-3:5432/messaging",
    "postgresql://postgres:postgres@postgres-4:5432/messaging",
    "postgresql://postgres:postgres@postgres-5:5432/messaging",
    "postgresql://postgres:postgres@postgres-6:5432/messaging",
    "postgresql://postgres:postgres@postgres-7:5432/messaging"
]

mongo_instances = [
    "mongodb://admin:admin@mongodb:27017/",
    "mongodb://admin:admin@mongodb-1:27017/",
    "mongodb://admin:admin@mongodb-2:27017/",
    "mongodb://admin:admin@mongodb-3:27017/",
    "mongodb://admin:admin@mongodb-4:27017/",
    "mongodb://admin:admin@mongodb-5:27017/",
    "mongodb://admin:admin@mongodb-6:27017/",
    "mongodb://admin:admin@mongodb-7:27017/"
]

batch_size = int(os.getenv("BATCH_SIZE", "1000"))
logical_shards_per_instance = int(os.getenv("LOGICAL_SHARDS_PER_INSTANCE", "8"))
adaptive_batching = os.getenv("ADAPTIVE_BATCHING", "true").lower() == "true"
max_latency_ms = int(os.getenv("MAX_LATENCY_MS", "20"))
benchmark_mode = os.getenv("BENCHMARK_MODE", "false").lower() == "true"
test_mode = os.getenv("TEST_MODE", "full")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/")

required_vars = ["BATCH_SIZE", "MAX_LATENCY_MS", "TEST_MODE"]
missing_vars = [var for var in required_vars if var not in os.environ]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {missing_vars}")
    sys.exit(1)

print(f"Configuration:")
print(f"  BATCH_SIZE: {batch_size}")
print(f"  LOGICAL_SHARDS_PER_INSTANCE: {logical_shards_per_instance}")
print(f"  ADAPTIVE_BATCHING: {adaptive_batching}")
print(f"  MAX_LATENCY_MS: {max_latency_ms}")
print(f"  BENCHMARK_MODE: {benchmark_mode}")
print(f"  TEST_MODE: {test_mode}")
print(f"  REDIS_URL: {redis_url}")

sharding_config = ShardingConfig(
    logical_shards_per_instance=logical_shards_per_instance,
    batch_size=batch_size,
    adaptive_batching=adaptive_batching,
    max_latency_ms=max_latency_ms
)

sharded_database = HorizontallyShardedDatabaseAdapter(
    postgres_instances=postgres_instances,
    mongo_instances=mongo_instances,
    config=sharding_config
)

queue_config = QueueConfig(max_size=100000, per_shard_limit=10000, enable_priority=True)
event_queue = InMemoryQueue(queue_config)

idempotency_store = None
if redis_url:
    try:
        idempotency_store = RedisIdempotencyStore(redis_url, ttl_seconds=3600)
        print("Redis idempotency store initialized")
    except Exception as e:
        print(f"WARNING: Failed to initialize Redis: {e}")

metrics = MetricsCollector(window_size=1000)

mock_schema_registry = MockSchemaRegistry()
mock_event_handler = EventHandler(sharded_database)
mock_producer = MockProducer()
mock_consumer = MockConsumer()
mock_broker = MockBroker()

api_config = DatabaseAPIConfig(
    event_writer=sharded_database,
    event_reader=sharded_database,
    event_manager=sharded_database,
    offset_port=sharded_database,
    count_port=sharded_database,
    queue=event_queue,
    idempotency_store=idempotency_store,
    metrics=metrics
)

database_api = DatabaseAPI(api_config)
schema_registry_api = SchemaRegistryAPI(mock_schema_registry)
event_handler_api = EventHandlerAPI(mock_event_handler)
producer_api = ProducerAPI(mock_producer)
consumer_api = ConsumerAPI(mock_consumer)
broker_api = BrokerAPI(mock_broker)

app.include_router(database_api.router, prefix="/api/v1/database", tags=["Database"])
app.include_router(schema_registry_api.router, prefix="/api/v1/schema-registry", tags=["Schema Registry"])
app.include_router(event_handler_api.router, prefix="/api/v1/event-handler", tags=["Event Handler"])
app.include_router(producer_api.router, prefix="/api/v1/producer", tags=["Producer"])
app.include_router(consumer_api.router, prefix="/api/v1/consumer", tags=["Consumer"])
app.include_router(broker_api.router, prefix="/api/v1/broker", tags=["Broker"])

app.add_middleware(LoggingMiddleware)
app.add_middleware(SanitizationMiddleware, max_body_size=1024 * 1024)
app.add_middleware(AuthMiddleware, api_key=None, skip_paths=["/health", "/metrics", "/docs", "/openapi.json"])


@app.get("/health")
def health():
    queue_stats = event_queue.get_stats()
    return {
        "status": "healthy",
        "database": "connected",
        "shards": sharded_database.total_shards,
        "batch_size": sharded_database.current_batch_size,
        "adaptive_batching": adaptive_batching,
        "queue_depth": queue_stats.total_size,
        "queue_dropped": queue_stats.dropped_count,
        "queue_rejections": queue_stats.rejection_count,
        "test_mode": test_mode,
        "benchmark_mode": benchmark_mode
    }


@app.get("/metrics")
def get_metrics():
    return metrics.get_all_metrics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "loadtests.test_server_realistic:app",
        host="0.0.0.0",
        port=8001,
        limit_concurrency=4000,
        limit_max_requests=1000000,
        timeout_keep_alive=30,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
