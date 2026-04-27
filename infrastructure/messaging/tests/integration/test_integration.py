import pytest
import os
from datetime import datetime
from infrastructure.adapters.postgres_database_adapter import PostgresDatabaseAdapter
from infrastructure.adapters.mongodb_database_adapter import MongoDatabaseAdapter
from infrastructure.adapters.confluent_schema_registry_adapter import ConfluentSchemaRegistryAdapter
from domain.ports.database_port import EventRecord, ConsumerOffset
from domain.ports.schema_registry_port import SchemaType


@pytest.mark.integration
class TestPostgreSQLAdapterIntegration:
    @pytest.fixture
    def postgres_dsn(self):
        return os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/test_db")

    @pytest.fixture
    def adapter(self, postgres_dsn):
        adapter = PostgresDatabaseAdapter(dsn=postgres_dsn)
        yield adapter
        adapter.close()

    def test_save_and_get_event(self, adapter):
        event = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        event_id = adapter.save_event(event)
        assert event_id is not None

        retrieved = adapter.get_event(event_id)
        assert retrieved.topic == event.topic
        assert retrieved.partition == event.partition
        assert retrieved.offset == event.offset

    def test_get_events_by_topic(self, adapter):
        event = EventRecord(
            topic="integration-test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        adapter.save_event(event)

        events = adapter.get_events_by_topic("integration-test-topic", limit=10)
        assert len(events) >= 1
        assert any(e.topic == "integration-test-topic" for e in events)

    def test_save_and_get_offset(self, adapter):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        result = adapter.save_offset(offset)
        assert result is True

        retrieved = adapter.get_offset("test-group", "test-topic", 0)
        assert retrieved.offset == 100

    def test_update_offset(self, adapter):
        offset = ConsumerOffset(
            consumer_group="test-group-update",
            topic="test-topic",
            partition=0,
            offset=100
        )
        adapter.save_offset(offset)

        offset.offset = 200
        adapter.save_offset(offset)

        retrieved = adapter.get_offset("test-group-update", "test-topic", 0)
        assert retrieved.offset == 200


@pytest.mark.integration
class TestMongoDBAdapterIntegration:
    @pytest.fixture
    def mongodb_uri(self):
        return os.getenv("MONGODB_URI", "mongodb://admin:admin@localhost:27017/")

    @pytest.fixture
    def adapter(self, mongodb_uri):
        adapter = MongoDatabaseAdapter(uri=mongodb_uri, database_name="test_db")
        yield adapter
        adapter.close()

    def test_save_and_get_event(self, adapter):
        event = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        event_id = adapter.save_event(event)
        assert event_id is not None

        retrieved = adapter.get_event(event_id)
        assert retrieved.topic == event.topic
        assert retrieved.partition == event.partition

    def test_get_events_by_topic(self, adapter):
        event = EventRecord(
            topic="integration-test-topic-mongo",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        adapter.save_event(event)

        events = adapter.get_events_by_topic("integration-test-topic-mongo", limit=10)
        assert len(events) >= 1

    def test_save_and_get_offset(self, adapter):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        result = adapter.save_offset(offset)
        assert result is True

        retrieved = adapter.get_offset("test-group", "test-topic", 0)
        assert retrieved.offset == 100

    def test_update_offset(self, adapter):
        offset = ConsumerOffset(
            consumer_group="test-group-update",
            topic="test-topic",
            partition=0,
            offset=100
        )
        adapter.save_offset(offset)

        offset.offset = 200
        adapter.save_offset(offset)

        retrieved = adapter.get_offset("test-group-update", "test-topic", 0)
        assert retrieved.offset == 200


@pytest.mark.integration
class TestSchemaRegistryAdapterIntegration:
    @pytest.fixture
    def schema_registry_url(self):
        return os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

    @pytest.fixture
    def adapter(self, schema_registry_url):
        adapter = ConfluentSchemaRegistryAdapter(url=schema_registry_url)
        yield adapter
        adapter.close()

    def test_register_and_get_schema(self, adapter):
        subject = "test-subject-integration"
        schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
        
        schema_id = adapter.register_schema(subject, schema, SchemaType.AVRO)
        assert schema_id > 0

        retrieved = adapter.get_schema(schema_id)
        assert retrieved.subject == subject
        assert retrieved.schema_type == SchemaType.AVRO

    def test_get_schema_by_subject(self, adapter):
        subject = "test-subject-by-subject"
        schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
        
        adapter.register_schema(subject, schema, SchemaType.AVRO)
        retrieved = adapter.get_schema_by_subject(subject)
        assert retrieved.subject == subject

    def test_list_subjects(self, adapter):
        subject = "test-subject-list"
        schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
        
        adapter.register_schema(subject, schema, SchemaType.AVRO)
        subjects = adapter.list_subjects()
        assert subject in subjects

    def test_check_compatibility(self, adapter):
        subject = "test-subject-compat"
        schema1 = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
        schema2 = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"},{"name":"name","type":"string","default":""}]}'
        
        adapter.register_schema(subject, schema1, SchemaType.AVRO)
        is_compatible = adapter.check_compatibility(subject, schema2, SchemaType.AVRO)
        assert is_compatible is True

    def test_delete_subject(self, adapter):
        subject = "test-subject-delete"
        schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
        
        adapter.register_schema(subject, schema, SchemaType.AVRO)
        result = adapter.delete_subject(subject)
        assert result is True

        subjects = adapter.list_subjects()
        assert subject not in subjects


@pytest.mark.integration
class TestEndToEndIntegration:
    @pytest.fixture
    def postgres_dsn(self):
        return os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/test_db")

    @pytest.fixture
    def mongodb_uri(self):
        return os.getenv("MONGODB_URI", "mongodb://admin:admin@localhost:27017/")

    @pytest.fixture
    def schema_registry_url(self):
        return os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")

    def test_postgres_and_schema_registry(self, postgres_dsn, schema_registry_url):
        db_adapter = PostgresDatabaseAdapter(dsn=postgres_dsn)
        schema_adapter = ConfluentSchemaRegistryAdapter(url=schema_registry_url)

        try:
            subject = "e2e-test-subject"
            schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
            
            schema_id = schema_adapter.register_schema(subject, schema, SchemaType.AVRO)
            assert schema_id > 0

            event = EventRecord(
                topic="e2e-topic",
                partition=0,
                offset=1,
                key="test-key",
                value='{"data": "test"}',
                timestamp=datetime.now()
            )
            event_id = db_adapter.save_event(event)
            assert event_id is not None

            retrieved = db_adapter.get_event(event_id)
            assert retrieved.topic == event.topic

        finally:
            db_adapter.close()
            schema_adapter.close()

    def test_mongodb_and_schema_registry(self, mongodb_uri, schema_registry_url):
        db_adapter = MongoDatabaseAdapter(uri=mongodb_uri, database_name="test_db")
        schema_adapter = ConfluentSchemaRegistryAdapter(url=schema_registry_url)

        try:
            subject = "e2e-mongo-subject"
            schema = '{"type":"record","name":"Test","fields":[{"name":"id","type":"int"}]}'
            
            schema_id = schema_adapter.register_schema(subject, schema, SchemaType.AVRO)
            assert schema_id > 0

            event = EventRecord(
                topic="e2e-mongo-topic",
                partition=0,
                offset=1,
                key="test-key",
                value='{"data": "test"}',
                timestamp=datetime.now()
            )
            event_id = db_adapter.save_event(event)
            assert event_id is not None

            retrieved = db_adapter.get_event(event_id)
            assert retrieved.topic == event.topic

        finally:
            db_adapter.close()
            schema_adapter.close()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
