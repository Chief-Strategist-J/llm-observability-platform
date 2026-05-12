import os
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Dict, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace import _Span

if not hasattr(_Span, 'record_error'):
    _Span.record_error = _Span.record_exception

trace.set_tracer_provider(TracerProvider())

from kafka_messaging_internal.shared.di.container import DIContainer, reset_container, get_container
from kafka_messaging_internal.shared.ports.database_port import DatabasePort
from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort, SchemaType


@pytest.fixture(scope="session")
def test_config() -> Dict[str, str]:
    """Test configuration fixture."""
    return {
        'DATABASE_TYPE': 'postgresql',
        'POSTGRES_DSN': os.getenv('POSTGRES_DSN', 'postgresql://test:test@localhost:5433/kafka_events_test'),
        'SCHEMA_REGISTRY_URL': os.getenv('TEST_SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
        'KAFKA_BOOTSTRAP_SERVERS': os.getenv('TEST_KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'DEPLOYMENT_ENV': 'test',
        'OTEL_SERVICE_NAME': 'kafka-messaging-internal-test',
        'OTEL_SERVICE_VERSION': '1.0.0-test',
        'HOST_NAME': 'test-host'
    }


@pytest.fixture
def di_container(test_config: Dict[str, str], mock_database_port, mock_schema_registry_port) -> DIContainer:
    """DI container fixture with test configuration."""
    reset_container()
    container = DIContainer()
    
    # Override configuration
    for key, value in test_config.items():
        container._config[key] = value
    
    # Register mock services
    container.register_singleton(DatabasePort, mock_database_port)
    container.register_singleton(SchemaRegistryPort, mock_schema_registry_port)
    
    return container


@pytest.fixture
def mock_database_port() -> Mock:
    """Mock database port fixture."""
    mock = Mock(spec=DatabasePort)
    
    # Setup default return values
    mock.save_event = AsyncMock(return_value="test-event-id")
    mock.save_events_batch = AsyncMock(side_effect=lambda records: [record.event_id for record in records])
    mock.get_event = AsyncMock(return_value=None)
    
    class MockEvent:
        def __init__(self, event_data):
            self.event_id = event_data["event_id"]
            self.topic = event_data["topic"]
            self.partition = event_data["partition"]
            self.offset = event_data["offset"]
            self.key = event_data["key"]
            self.value = event_data["value"]
            self.timestamp = event_data["timestamp"]
            self.headers = event_data.get("headers", {})
        
        def to_dict(self):
            return {
                "event_id": self.event_id,
                "topic": self.topic,
                "partition": self.partition,
                "offset": self.offset,
                "key": self.key,
                "value": self.value,
                "timestamp": self.timestamp,
                "headers": self.headers
            }
    
    def get_performance_events(topic="performance-test-topic", count=None):
        """Generate performance test events."""
        event_count = count if count is not None else (100 if "performance" in topic else 1)
        
        return [MockEvent({
            "event_id": f"perf-event-{i}",
            "topic": topic,
            "partition": 0,
            "offset": i,
            "key": f"perf-key-{i}",
            "value": {"message": f"Performance test message {i}", "data": "x" * 100},
            "timestamp": "2025-01-11T12:00:00Z"
        }) for i in range(event_count)]

    mock.get_events_by_topic = AsyncMock(side_effect=lambda topic, limit=100, offset=0: (
        get_performance_events(topic, limit)[offset:offset+limit] if "performance-test-topic" in topic else []
    ))
    mock.get_unprocessed_events = AsyncMock(return_value=[])
    mock.mark_event_processed = AsyncMock(return_value=True)
    mock.save_consumer_offset = AsyncMock(return_value=True)
    from kafka_messaging_internal.shared.ports.database_port import ConsumerOffset
    
    mock.get_consumer_offset = AsyncMock(return_value=ConsumerOffset(
        consumer_group="test-workflow-group",
        topic="test-workflow-topic", 
        partition=0,
        offset=3
    ))
    mock.delete_events_by_topic = AsyncMock(return_value=0)
    mock.get_event_count = AsyncMock(side_effect=lambda topic: 100 if "performance" in topic else 3)
    mock.connect = AsyncMock(return_value=None)
    mock.disconnect = AsyncMock(return_value=None)
    mock.execute_query = AsyncMock(return_value=[])
    mock.execute_command = AsyncMock(return_value=1)
    mock.begin_transaction = AsyncMock(return_value=None)
    mock.commit_transaction = AsyncMock(return_value=None)
    mock.rollback_transaction = AsyncMock(return_value=None)
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock(return_value=None)
    
    return mock


@pytest.fixture
def mock_schema_registry_port() -> Mock:
    """Mock schema registry port fixture."""
    mock = Mock(spec=SchemaRegistryPort)
    
    # Setup default return values
    mock.register_schema = AsyncMock(side_effect=lambda schema: 1 if hasattr(schema, 'name') else 1)
    mock.check_compatibility = AsyncMock(return_value=True)
    mock.validate_schema = AsyncMock(return_value=True)
    mock.get_schema = AsyncMock(return_value=None)
    from kafka_messaging_internal.shared.ports.database_port import ConsumerOffset
    from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaInfo, SchemaType
    
    class MockSchemaInfo:
        def __init__(self, subject, schema_id, version, schema_type, definition, compatibility):
            self.subject = subject
            self.schema_id = schema_id
            self.version = version
            self.schema_type = schema_type
            self.definition = definition
            self.compatibility = compatibility
            self.name = subject  # Add name attribute for service compatibility
            self.id = schema_id      # Add id attribute for service compatibility
    
    mock.get_schema_by_name = AsyncMock(side_effect=lambda subject, version: MockSchemaInfo(
        subject="test-lifecycle-subject",
        schema_id=1,
        version=1,
        schema_type=SchemaType.AVRO,
        definition='{"type": "record", "name": "LifecycleEvent", "fields": [{"name": "message", "type": "string"}]}',
        compatibility="BACKWARD"
    ) if subject == "test-lifecycle-subject" and version is None else None)
    mock.get_schema_by_subject = AsyncMock(side_effect=lambda subject, version: {
        "subject": subject,
        "schema_id": 1,
        "version": 1,
        "schema_type": "AVRO",
        "schema": '{"type": "record", "name": "PerfRecord", "fields": [{"name": "message", "type": "string"}, {"name": "data", "type": "bytes"}]}',
        "compatibility": "BACKWARD"
    } if subject.startswith("performance-schema-") else (
        {
            "subject": "test-lifecycle-subject",
            "schema_id": 1,
            "version": 1,
            "schema_type": "AVRO",
            "schema": '{"type": "record", "name": "LifecycleEvent", "fields": [{"name": "message", "type": "string"}]}',
            "compatibility": "BACKWARD"
        } if subject == "test-lifecycle-subject" else {
            "subject": None,
            "schema_id": None,
            "version": None,
            "schema_type": None,
            "schema": None,
            "compatibility": None
        }
    ))
    mock.get_latest_schema = AsyncMock(return_value=None)
    mock.list_schemas = AsyncMock(return_value=[MockSchemaInfo(
        subject="test-lifecycle-subject",
        schema_id=1,
        version=1,
        schema_type=SchemaType.AVRO,
        definition='{"type": "record", "name": "LifecycleEvent", "fields": [{"name": "message", "type": "string"}]}',
        compatibility="BACKWARD"
    )])
    mock.list_subjects = AsyncMock(return_value=["test-lifecycle-subject"])
    mock.list_versions = AsyncMock(return_value=[])
    mock.delete_subject = AsyncMock(return_value=False)
    mock.check_compatibility = AsyncMock(return_value=True)
    mock.update_compatibility = AsyncMock(return_value=True)
    mock.serialize = AsyncMock(return_value=b'{"data": "test"}')
    mock.deserialize = AsyncMock(return_value={"test": "data"})
    mock.close = AsyncMock(return_value=None)
    
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
def setup_test_environment(mock_database_port, mock_schema_registry_port):
    """Setup test environment for all tests."""
    # Reset and setup container first
    reset_container()
    container = get_container()
    container.register_singleton(DatabasePort, mock_database_port)
    container.register_singleton(SchemaRegistryPort, mock_schema_registry_port)
    
    # Set test environment variables
    os.environ['DEPLOYMENT_ENV'] = 'test'
    os.environ['OTEL_SERVICE_NAME'] = 'kafka-messaging-internal-test'
    
    yield
    
    # Cleanup
    test_vars = ['DEPLOYMENT_ENV', 'OTEL_SERVICE_NAME']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]
