import pytest
from unittest.mock import Mock, MagicMock, patch
from infrastructure.adapters.kafka_producer_adapter import (
    HighThroughputKafkaProducer,
    KafkaProducerConfig
)
from infrastructure.adapters.kafka_consumer_adapter import (
    HighThroughputKafkaConsumer,
    KafkaConsumerConfig
)


@pytest.fixture
def producer_config():
    return KafkaProducerConfig(
        bootstrap_servers="localhost:9092",
        batch_size=65536,
        linger_ms=10,
        compression_type="snappy",
        acks="all"
    )


@pytest.fixture
def consumer_config():
    return KafkaConsumerConfig(
        bootstrap_servers="localhost:9092",
        group_id="test-group",
        max_threads=10
    )


class TestKafkaProducerConfig:
    def test_default_config(self):
        config = KafkaProducerConfig()
        assert config.batch_size == 65536
        assert config.linger_ms == 10
        assert config.compression_type == "snappy"
        assert config.acks == "all"
        assert config.enable_idempotence is True
    
    def test_custom_config(self):
        config = KafkaProducerConfig(
            batch_size=131072,
            linger_ms=20,
            compression_type="lz4",
            acks="all"
        )
        assert config.batch_size == 131072
        assert config.linger_ms == 20
        assert config.compression_type == "lz4"
        assert config.acks == "all"


class TestHighThroughputKafkaProducer:
    @patch('confluent_kafka.Producer')
    def test_init_with_confluent(self, mock_producer_class, producer_config):
        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer
        
        producer = HighThroughputKafkaProducer(producer_config)
        
        assert producer._producer is not None
        mock_producer_class.assert_called_once()
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_init_without_confluent(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        assert producer._producer is None
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_produce_mock(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        result = producer.produce("test-topic", "key", "value", 0, {})
        
        assert result["topic"] == "test-topic"
        assert result["partition"] == 0
        assert result["status"] == "mock"
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_produce_batch_mock(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        messages = [
            {"topic": "t1", "key": "k1", "value": "v1", "partition": 0, "headers": {}},
            {"topic": "t1", "key": "k2", "value": "v2", "partition": 0, "headers": {}}
        ]
        
        results = producer.produce_batch("test-topic", messages)
        
        assert len(results) == 2
        assert all(r["status"] == "mock" for r in results)
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_list_topics_mock(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        topics = producer.list_topics()
        
        assert "topic1" in topics
        assert "topic2" in topics
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    @patch('confluent_kafka.admin.AdminClient', side_effect=ImportError)
    def test_create_topic_mock(self, mock_admin, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        result = producer.create_topic("new-topic", 3, 2)
        
        assert result is True
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_flush_mock(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        producer.flush()
    
    @patch('confluent_kafka.Producer', side_effect=ImportError)
    def test_close(self, mock_producer, producer_config):
        producer = HighThroughputKafkaProducer(producer_config)
        producer.close()


class TestKafkaConsumerConfig:
    def test_default_config(self):
        config = KafkaConsumerConfig()
        assert config.group_id == "default-consumer-group"
        assert config.auto_offset_reset == "earliest"
        assert config.enable_auto_commit is False
        assert config.max_poll_records == 500
        assert config.max_threads == 10
    
    def test_custom_config(self):
        config = KafkaConsumerConfig(
            group_id="custom-group",
            max_poll_records=1000,
            max_threads=20
        )
        assert config.group_id == "custom-group"
        assert config.max_poll_records == 1000
        assert config.max_threads == 20


class TestHighThroughputKafkaConsumer:
    @patch('confluent_kafka.Consumer')
    def test_init_with_confluent(self, mock_consumer_class, consumer_config):
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        consumer = HighThroughputKafkaConsumer(consumer_config)
        
        assert consumer._consumer is not None
        mock_consumer_class.assert_called_once()
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_init_without_confluent(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        assert consumer._consumer is None
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_consume_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        messages = consumer.consume("test-topic", "group1", 0, 10, 1000)
        
        assert len(messages) == 10
        assert messages[0]["topic"] == "test-topic"
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_consume_parallel_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        partitions = [0, 1, 2]
        
        results = consumer.consume_parallel(
            "test-topic",
            "group1",
            partitions,
            100,
            1000
        )
        
        assert len(results) == 3
        assert all(isinstance(results[p], list) for p in partitions)
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_commit_offset_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        result = consumer.commit_offset("group1", "test-topic", 0, 100)
        
        assert result is True
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_commit_offsets_batch_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        offsets = {
            "topic1": {0: 100, 1: 200},
            "topic2": {0: 300}
        }
        
        result = consumer.commit_offsets_batch(offsets)
        
        assert result is True
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_get_offset_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        offset = consumer.get_offset("group1", "test-topic", 0)
        
        assert offset == 100
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_subscribe_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        result = consumer.subscribe("test-topic", "group1")
        
        assert result is True
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_unsubscribe_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        result = consumer.unsubscribe("test-topic", "group1")
        
        assert result is True
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_list_subscriptions_mock(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        subs = consumer.list_subscriptions("group1")
        
        assert "topic1" in subs
        assert "topic2" in subs
    
    @patch('confluent_kafka.Consumer', side_effect=ImportError)
    def test_close(self, mock_consumer, consumer_config):
        consumer = HighThroughputKafkaConsumer(consumer_config)
        consumer.close()


class TestPerformanceConfiguration:
    def test_producer_high_throughput_config(self):
        config = KafkaProducerConfig(
            batch_size=131072,  # 128KB
            linger_ms=20,
            compression_type="snappy",
            acks="all",
            max_in_flight_requests_per_connection=10
        )
        
        assert config.batch_size == 131072
        assert config.linger_ms == 20
        assert config.compression_type == "snappy"
    
    def test_consumer_high_throughput_config(self):
        config = KafkaConsumerConfig(
            max_poll_records=1000,
            max_threads=20,
            fetch_max_bytes=104857600,  # 100MB
            max_partition_fetch_bytes=10485760  # 10MB
        )
        
        assert config.max_poll_records == 1000
        assert config.max_threads == 20
        assert config.fetch_max_bytes == 104857600
