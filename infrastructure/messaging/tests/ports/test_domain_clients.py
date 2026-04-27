import pytest
from unittest.mock import Mock
from datetime import datetime

from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset
from domain.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo
from domain.ports.producer_port import ProducerPort, ProduceMessageParams, TopicCreationParams
from domain.ports.consumer_port import ConsumerPort, ConsumeParams, ConsumerOffsetParams
from domain.ports.broker_port import BrokerPort

from domain.clients.database_client import DatabaseDomainClient
from domain.clients.schema_registry_client import SchemaRegistryDomainClient
from domain.clients.producer_client import ProducerDomainClient
from domain.clients.consumer_client import ConsumerDomainClient
from domain.clients.broker_client import BrokerDomainClient


@pytest.fixture
def mock_database():
    database = Mock(spec=DatabasePort)
    database.save_event.return_value = "event-123"
    database.save_events_batch.return_value = ["id-1", "id-2"]
    database.get_event.return_value = EventRecord(
        topic="test", partition=0, offset=1, key="k", value="v",
        timestamp=datetime.now(), headers={}
    )
    database.get_events_by_topic.return_value = []
    database.get_unprocessed_events.return_value = []
    database.mark_event_processed.return_value = True
    database.save_consumer_offset.return_value = True
    database.get_consumer_offset.return_value = ConsumerOffset(
        consumer_group="g1", topic="t1", partition=0, offset=100
    )
    database.delete_events_by_topic.return_value = 5
    database.get_event_count.return_value = 100
    return database


@pytest.fixture
def mock_schema_registry():
    registry = Mock(spec=SchemaRegistryPort)
    registry.register_schema.return_value = 1
    registry.get_schema.return_value = SchemaInfo(
        subject="test", schema_id=1, schema_type=SchemaType.AVRO,
        schema='{"type":"record"}', version=1
    )
    registry.get_schema_by_subject.return_value = SchemaInfo(
        subject="test", schema_id=1, schema_type=SchemaType.AVRO,
        schema='{"type":"record"}', version=1
    )
    registry.get_latest_schema.return_value = SchemaInfo(
        subject="test", schema_id=1, schema_type=SchemaType.AVRO,
        schema='{"type":"record"}', version=1
    )
    registry.list_subjects.return_value = ["subject1", "subject2"]
    registry.list_versions.return_value = [1, 2, 3]
    registry.delete_subject.return_value = True
    registry.check_compatibility.return_value = True
    registry.update_compatibility.return_value = True
    registry.serialize.return_value = b"serialized"
    registry.deserialize.return_value = {"key": "value"}
    return registry


@pytest.fixture
def mock_producer():
    producer = Mock(spec=ProducerPort)
    producer.produce.return_value = {"topic": "t1", "offset": 100}
    producer.list_topics.return_value = ["topic1", "topic2"]
    producer.create_topic.return_value = True
    return producer


@pytest.fixture
def mock_consumer():
    consumer = Mock(spec=ConsumerPort)
    consumer.consume.return_value = [{"key": "value"}]
    consumer.commit_offset.return_value = True
    consumer.get_offset.return_value = 100
    consumer.subscribe.return_value = True
    consumer.unsubscribe.return_value = True
    consumer.list_subscriptions.return_value = ["topic1", "topic2"]
    return consumer


@pytest.fixture
def mock_broker():
    broker = Mock(spec=BrokerPort)
    broker.get_broker_metadata.return_value = {"cluster_id": "test", "broker_count": 3}
    broker.list_brokers.return_value = [{"broker_id": 1}]
    broker.get_broker_info.return_value = {"broker_id": 1, "host": "localhost"}
    broker.list_topics.return_value = ["topic1", "topic2"]
    broker.get_topic_metadata.return_value = {"topic_name": "t1", "partitions": 3}
    broker.get_consumer_groups.return_value = [{"group_id": "g1"}]
    broker.get_consumer_group_lag.return_value = [{"group_id": "g1", "lag": 50}]
    broker.get_cluster_config.return_value = {"key": "value"}
    return broker


class TestDatabaseDomainClient:
    def test_save_event(self, mock_database):
        client = DatabaseDomainClient(mock_database)
        result = client.save_event("test-topic", 0, 100, "key", "value")
        
        assert result == "event-123"
        mock_database.save_event.assert_called_once()
    
    def test_save_events_batch(self, mock_database):
        client = DatabaseDomainClient(mock_database)
        result = client.save_events_batch([
            {"topic": "t1", "partition": 0, "offset": 1},
            {"topic": "t2", "partition": 0, "offset": 2}
        ])
        
        assert len(result) == 2
        mock_database.save_events_batch.assert_called_once()
    
    def test_get_event(self, mock_database):
        client = DatabaseDomainClient(mock_database)
        result = client.get_event("event-123")
        
        assert result.topic == "test"
        mock_database.get_event.assert_called_once_with("event-123")
    
    def test_save_consumer_offset(self, mock_database):
        client = DatabaseDomainClient(mock_database)
        result = client.save_consumer_offset("g1", "t1", 0, 100)
        
        assert result is True
        mock_database.save_consumer_offset.assert_called_once()
    
    def test_get_consumer_offset(self, mock_database):
        client = DatabaseDomainClient(mock_database)
        result = client.get_consumer_offset("g1", "t1", 0)
        
        assert result.offset == 100
        mock_database.get_consumer_offset.assert_called_once()


class TestSchemaRegistryDomainClient:
    def test_register_schema(self, mock_schema_registry):
        client = SchemaRegistryDomainClient(mock_schema_registry)
        result = client.register_schema("test-subject", '{"type":"record"}')
        
        assert result == 1
        mock_schema_registry.register_schema.assert_called_once()
    
    def test_get_schema(self, mock_schema_registry):
        client = SchemaRegistryDomainClient(mock_schema_registry)
        result = client.get_schema(1)
        
        assert result.schema_id == 1
        mock_schema_registry.get_schema.assert_called_once_with(1)
    
    def test_list_subjects(self, mock_schema_registry):
        client = SchemaRegistryDomainClient(mock_schema_registry)
        result = client.list_subjects()
        
        assert "subject1" in result
        mock_schema_registry.list_subjects.assert_called_once()
    
    def test_serialize(self, mock_schema_registry):
        client = SchemaRegistryDomainClient(mock_schema_registry)
        result = client.serialize("test-subject", {"key": "value"})
        
        assert result == b"serialized"
        mock_schema_registry.serialize.assert_called_once()
    
    def test_deserialize(self, mock_schema_registry):
        client = SchemaRegistryDomainClient(mock_schema_registry)
        result = client.deserialize(b"data", 1)
        
        assert result["key"] == "value"
        mock_schema_registry.deserialize.assert_called_once()


class TestProducerDomainClient:
    def test_produce(self, mock_producer):
        client = ProducerDomainClient(mock_producer)
        result = client.produce("test-topic", "value", "key")
        
        assert result["offset"] == 100
        mock_producer.produce.assert_called_once()
    
    def test_list_topics(self, mock_producer):
        client = ProducerDomainClient(mock_producer)
        result = client.list_topics()
        
        assert "topic1" in result
        mock_producer.list_topics.assert_called_once()
    
    def test_create_topic(self, mock_producer):
        client = ProducerDomainClient(mock_producer)
        result = client.create_topic("new-topic", 3, 2)
        
        assert result is True
        mock_producer.create_topic.assert_called_once()


class TestConsumerDomainClient:
    def test_consume(self, mock_consumer):
        client = ConsumerDomainClient(mock_consumer)
        result = client.consume("test-topic", "group1")
        
        assert len(result) == 1
        mock_consumer.consume.assert_called_once()
    
    def test_commit_offset(self, mock_consumer):
        client = ConsumerDomainClient(mock_consumer)
        result = client.commit_offset("group1", "test-topic", 0, 100)
        
        assert result is True
        mock_consumer.commit_offset.assert_called_once()
    
    def test_subscribe(self, mock_consumer):
        client = ConsumerDomainClient(mock_consumer)
        result = client.subscribe("test-topic", "group1")
        
        assert result is True
        mock_consumer.subscribe.assert_called_once()
    
    def test_list_subscriptions(self, mock_consumer):
        client = ConsumerDomainClient(mock_consumer)
        result = client.list_subscriptions("group1")
        
        assert "topic1" in result
        mock_consumer.list_subscriptions.assert_called_once()


class TestBrokerDomainClient:
    def test_get_broker_metadata(self, mock_broker):
        client = BrokerDomainClient(mock_broker)
        result = client.get_broker_metadata()
        
        assert result["cluster_id"] == "test"
        mock_broker.get_broker_metadata.assert_called_once()
    
    def test_list_brokers(self, mock_broker):
        client = BrokerDomainClient(mock_broker)
        result = client.list_brokers()
        
        assert len(result) == 1
        mock_broker.list_brokers.assert_called_once()
    
    def test_get_topic_metadata(self, mock_broker):
        client = BrokerDomainClient(mock_broker)
        result = client.get_topic_metadata("test-topic")
        
        assert result["topic_name"] == "t1"
        mock_broker.get_topic_metadata.assert_called_once()
    
    def test_get_consumer_groups(self, mock_broker):
        client = BrokerDomainClient(mock_broker)
        result = client.get_consumer_groups()
        
        assert len(result) == 1
        mock_broker.get_consumer_groups.assert_called_once()
