import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from infrastructure.messaging.application.clients.base_client import BaseClient, ClientConfig
from infrastructure.messaging.application.clients.database_client import DatabaseClient
from infrastructure.messaging.application.clients.schema_registry_client import SchemaRegistryClient
from infrastructure.messaging.application.clients.event_handler_client import EventHandlerClient, SchemaAwareEventHandlerClient
from infrastructure.messaging.application.clients.producer_client import ProducerClient
from infrastructure.messaging.application.clients.consumer_client import ConsumerClient
from infrastructure.messaging.application.clients.broker_client import BrokerClient


@pytest.fixture
def client_config():
    return ClientConfig(
        base_url="http://localhost:8001",
        api_key="test-key",
        timeout=30
    )


class TestBaseClient:
    def test_init_with_api_key(self, client_config):
        client = BaseClient(client_config)
        assert client.base_url == "http://localhost:8001"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-key"
        client.close()
    
    def test_init_without_api_key(self):
        config = ClientConfig(base_url="http://localhost:8001")
        client = BaseClient(config)
        assert client.base_url == "http://localhost:8001"
        assert "Authorization" not in client.headers
        client.close()
    
    def test_context_manager(self, client_config):
        with BaseClient(client_config) as client:
            assert client is not None
    
    @patch('httpx.Client.request')
    def test_get_request(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = BaseClient(client_config)
        result = client.get("/test")
        
        assert result == {"data": "test"}
        mock_request.assert_called_once()
        client.close()
    
    @patch('httpx.Client.request')
    def test_post_request(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = BaseClient(client_config)
        result = client.post("/test", {"key": "value"})
        
        assert result == {"success": True}
        mock_request.assert_called_once()
        client.close()


class TestDatabaseClient:
    @patch('httpx.Client.request')
    def test_save_event(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"event_id": "123"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = DatabaseClient(client_config)
        result = client.save_event("test-topic", 0, 100, "key", "value")
        
        assert result["event_id"] == "123"
        client.close()
    
    @patch('httpx.Client.request')
    def test_save_events_batch(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"count": 3}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = DatabaseClient(client_config)
        result = client.save_events_batch([{"topic": "t1"}, {"topic": "t2"}])
        
        assert result["count"] == 3
        client.close()
    
    @patch('httpx.Client.request')
    def test_get_event(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"event_id": "123", "topic": "test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = DatabaseClient(client_config)
        result = client.get_event("123")
        
        assert result["event_id"] == "123"
        client.close()


class TestSchemaRegistryClient:
    @patch('httpx.Client.request')
    def test_register_schema(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"schema_id": 1}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = SchemaRegistryClient(client_config)
        result = client.register_schema("test-subject", '{"type":"record"}')
        
        assert result["schema_id"] == 1
        client.close()
    
    @patch('httpx.Client.request')
    def test_get_schema(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"schema_id": 1, "subject": "test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = SchemaRegistryClient(client_config)
        result = client.get_schema(1)
        
        assert result["schema_id"] == 1
        client.close()


class TestEventHandlerClient:
    @patch('httpx.Client.request')
    def test_process_record(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"event_id": "123"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = EventHandlerClient(client_config)
        result = client.process_record("test-topic", 0, 100, "key", "value")
        
        assert result["event_id"] == "123"
        client.close()


class TestProducerClient:
    @patch('httpx.Client.request')
    def test_produce_message(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "offset": 100}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = ProducerClient(client_config)
        result = client.produce_message("test-topic", "value", "key")
        
        assert result["success"] is True
        client.close()
    
    @patch('httpx.Client.request')
    def test_list_topics(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"topics": ["topic1", "topic2"]}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = ProducerClient(client_config)
        result = client.list_topics()
        
        assert "topic1" in result["topics"]
        client.close()


class TestConsumerClient:
    @patch('httpx.Client.request')
    def test_consume_messages(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"messages": [{"key": "value"}]}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = ConsumerClient(client_config)
        result = client.consume_messages("test-topic", "group1")
        
        assert len(result["messages"]) == 1
        client.close()
    
    @patch('httpx.Client.request')
    def test_commit_offset(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = ConsumerClient(client_config)
        result = client.commit_offset("group1", "test-topic", 0, 100)
        
        assert result["success"] is True
        client.close()


class TestBrokerClient:
    @patch('httpx.Client.request')
    def test_get_broker_metadata(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = {"cluster_id": "test-cluster", "broker_count": 3}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = BrokerClient(client_config)
        result = client.get_broker_metadata()
        
        assert result["cluster_id"] == "test-cluster"
        client.close()
    
    @patch('httpx.Client.request')
    def test_list_brokers(self, mock_request, client_config):
        mock_response = Mock()
        mock_response.json.return_value = [{"broker_id": 1}, {"broker_id": 2}]
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        client = BrokerClient(client_config)
        result = client.list_brokers()
        
        assert len(result) == 2
        client.close()
