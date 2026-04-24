from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from unittest.mock import Mock
from datetime import datetime

from infrastructure.messaging.application.api.v1.database_api import DatabaseAPI
from infrastructure.messaging.application.api.v1.schema_registry_api import SchemaRegistryAPI
from infrastructure.messaging.application.api.v1.event_handler_api import EventHandlerAPI, SchemaAwareEventHandlerAPI
from infrastructure.messaging.application.api.v1.producer_api import ProducerAPI
from infrastructure.messaging.application.api.v1.consumer_api import ConsumerAPI
from infrastructure.messaging.application.api.v1.broker_api import BrokerAPI
from infrastructure.messaging.domain.ports.database_port import EventRecord, ConsumerOffset, DatabasePort
from infrastructure.messaging.domain.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo
from infrastructure.messaging.domain.ports.producer_port import ProducerPort
from infrastructure.messaging.domain.ports.consumer_port import ConsumerPort
from infrastructure.messaging.domain.ports.broker_port import BrokerPort
from infrastructure.messaging.domain.services.event_handler import EventHandler
from infrastructure.messaging.domain.services.schema_aware_event_handler import SchemaAwareEventHandler


class MockDatabase(DatabasePort):
    def save_event(self, event: EventRecord) -> str:
        return "event-id-123"
    
    def save_events_batch(self, events: list) -> list:
        return [f"id-{i}" for i in range(len(events))]
    
    def get_event(self, event_id: str) -> EventRecord:
        return EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="key",
            value="value",
            timestamp=datetime.now(),
            headers={}
        )
    
    def get_events_by_topic(self, topic: str, limit: int, offset: int) -> list:
        return []
    
    def get_unprocessed_events(self, limit: int) -> list:
        return []
    
    def mark_event_processed(self, event_id: str) -> bool:
        return True
    
    def save_consumer_offset(self, offset) -> bool:
        return True
    
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        return ConsumerOffset(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=100
        )
    
    def delete_events_by_topic(self, topic: str) -> int:
        return 5
    
    def get_event_count(self, topic: str) -> int:
        return 100
    
    def close(self):
        pass


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
    
    def list_subjects(self) -> list:
        return ["subject1", "subject2"]
    
    def list_versions(self, subject: str) -> list:
        return [1, 2, 3]
    
    def delete_subject(self, subject: str) -> bool:
        return True
    
    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        return True
    
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        return True
    
    def serialize(self, subject: str, data: dict, schema_id: int = None) -> bytes:
        return b"serialized-data"
    
    def deserialize(self, data: bytes, schema_id: int) -> dict:
        return {"key": "value"}
    
    def close(self):
        pass


class MockProducer(ProducerPort):
    def produce(self, topic: str, key: str, value: dict, partition: int, headers: dict) -> dict:
        return {"topic": topic, "partition": partition or 0, "offset": 100, "timestamp": 1234567890}
    
    def list_topics(self) -> list:
        return ["topic1", "topic2"]
    
    def create_topic(self, topic_name: str, partitions: int, replication_factor: int) -> bool:
        return True


class MockConsumer(ConsumerPort):
    def consume(self, topic: str, consumer_group: str, partition: int, max_messages: int, timeout_ms: int) -> list:
        return [{"topic": topic, "partition": 0, "offset": 100, "key": "key", "value": "value", "timestamp": 1234567890, "headers": {}}]
    
    def commit_offset(self, consumer_group: str, topic: str, partition: int, offset: int) -> bool:
        return True
    
    def get_offset(self, consumer_group: str, topic: str, partition: int) -> int:
        return 100
    
    def subscribe(self, topic: str, consumer_group: str) -> bool:
        return True
    
    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        return True
    
    def list_subscriptions(self, consumer_group: str) -> list:
        return ["topic1", "topic2"]


class MockBroker(BrokerPort):
    def get_broker_metadata(self) -> dict:
        return {"cluster_id": "test-cluster", "controller_id": 1, "broker_count": 3, "topic_count": 10}
    
    def list_brokers(self) -> list:
        return [{"broker_id": 1, "host": "localhost", "port": 9092, "rack": "rack1"}]
    
    def get_broker_info(self, broker_id: int) -> dict:
        return {"broker_id": broker_id, "host": "localhost", "port": 9092, "rack": "rack1"}
    
    def list_topics(self) -> list:
        return ["topic1", "topic2", "topic3"]
    
    def get_topic_metadata(self, topic_name: str) -> dict:
        return {"topic_name": topic_name, "partition_count": 3, "replication_factor": 2, "partitions": []}
    
    def get_consumer_groups(self) -> list:
        return [{"group_id": "group1", "state": "Stable", "members": 3, "topics": ["topic1"]}]
    
    def get_consumer_group_lag(self, group_id: str) -> list:
        return [{"group_id": group_id, "topic": "topic1", "partition": 0, "current_offset": 100, "log_end_offset": 150, "lag": 50}]
    
    def get_cluster_config(self) -> dict:
        return {"num.partitions": "3", "default.replication.factor": "2"}


app = FastAPI(title="Messaging API Test Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mock_database = MockDatabase()
mock_schema_registry = MockSchemaRegistry()
mock_event_handler = EventHandler(mock_database)
mock_producer = MockProducer()
mock_consumer = MockConsumer()
mock_broker = MockBroker()

database_api = DatabaseAPI(mock_database)
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


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
