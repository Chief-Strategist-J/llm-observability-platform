"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from kafka_messaging_internal.shared.di.container import DIContainer, reset_container
from kafka_messaging_internal.shared.ports.database_port import DatabasePort
from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort


@pytest.fixture(scope="session")
def test_config() -> Dict[str, str]:
    """Test configuration fixture."""
    return {
        'DATABASE_TYPE': 'postgresql',
        'POSTGRES_DSN': os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/kafka_events_test'),
        'SCHEMA_REGISTRY_URL': os.getenv('TEST_SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
        'KAFKA_BOOTSTRAP_SERVERS': os.getenv('TEST_KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'DEPLOYMENT_ENV': 'test',
        'OTEL_SERVICE_NAME': 'kafka-messaging-internal-test',
        'OTEL_SERVICE_VERSION': '1.0.0-test',
        'HOST_NAME': 'test-host'
    }


@pytest.fixture
def di_container(test_config: Dict[str, str]) -> DIContainer:
    """DI container fixture with test configuration."""
    reset_container()
    container = DIContainer()
    
    # Override configuration
    for key, value in test_config.items():
        container._config[key] = value
    
    return container


@pytest.fixture
def mock_database_port() -> Mock:
    """Mock database port fixture."""
    mock = Mock(spec=DatabasePort)
    
    # Setup default return values
    mock.save_event.return_value = "test-event-id"
    mock.save_events_batch.return_value = ["test-event-id-1", "test-event-id-2"]
    mock.get_event.return_value = None
    mock.get_events_by_topic.return_value = []
    mock.get_unprocessed_events.return_value = []
    mock.mark_event_processed.return_value = True
    mock.save_consumer_offset.return_value = True
    mock.get_consumer_offset.return_value = None
    mock.delete_events_by_topic.return_value = 0
    mock.get_event_count.return_value = 0
    mock.close.return_value = None
    
    return mock


@pytest.fixture
def mock_schema_registry_port() -> Mock:
    """Mock schema registry port fixture."""
    mock = Mock(spec=SchemaRegistryPort)
    
    # Setup default return values
    mock.register_schema.return_value = 1
    mock.get_schema.return_value = None
    mock.get_schema_by_subject.return_value = None
    mock.get_latest_schema.return_value = None
    mock.list_subjects.return_value = []
    mock.list_versions.return_value = []
    mock.delete_subject.return_value = False
    mock.check_compatibility.return_value = True
    mock.update_compatibility.return_value = True
    mock.serialize.return_value = b"serialized-data"
    mock.deserialize.return_value = {"test": "data"}
    mock.close.return_value = None
    
    return mock


@pytest.fixture
def sample_event_data() -> Dict[str, Any]:
    """Sample event data fixture."""
    return {
        "event_id": "test-event-123",
        "topic": "test-topic",
        "partition": 0,
        "offset": 123,
        "key": "test-key",
        "value": {"message": "test data", "timestamp": "2025-01-11T12:00:00Z"},
        "timestamp": "2025-01-11T12:00:00Z",
        "headers": {"source": "test", "version": "1.0"}
    }


@pytest.fixture
def sample_schema_data() -> Dict[str, Any]:
    """Sample schema data fixture."""
    return {
        "subject": "test-subject",
        "schema": '{"type": "record", "name": "TestRecord", "fields": [{"name": "message", "type": "string"}]}',
        "schema_type": "AVRO"
    }


@pytest.fixture
def sample_batch_events() -> list[Dict[str, Any]]:
    """Sample batch events fixture."""
    return [
        {
            "event_id": "test-event-1",
            "topic": "test-topic",
            "partition": 0,
            "offset": 1,
            "key": "test-key-1",
            "value": {"message": "test data 1"},
            "timestamp": "2025-01-11T12:00:00Z"
        },
        {
            "event_id": "test-event-2",
            "topic": "test-topic",
            "partition": 0,
            "offset": 2,
            "key": "test-key-2",
            "value": {"message": "test data 2"},
            "timestamp": "2025-01-11T12:00:01Z"
        }
    ]


@pytest.fixture
def sample_consumer_offset_data() -> Dict[str, Any]:
    """Sample consumer offset data fixture."""
    return {
        "consumer_group": "test-group",
        "topic": "test-topic",
        "partition": 0,
        "offset": 123
    }


# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "contract: Contract tests"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests"
    )


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests."""
    # Set test environment variables
    os.environ['DEPLOYMENT_ENV'] = 'test'
    os.environ['OTEL_SERVICE_NAME'] = 'kafka-messaging-internal-test'
    
    yield
    
    # Cleanup
    test_vars = ['DEPLOYMENT_ENV', 'OTEL_SERVICE_NAME']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]
