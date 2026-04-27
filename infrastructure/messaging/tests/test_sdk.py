import pytest
from unittest.mock import Mock, MagicMock, patch
from infrastructure.messaging.sdk import MessagingSDK, create_postgres_sdk, create_mongodb_sdk, create_schema_registry_sdk
from domain.models.schemas import DatabaseConfig, SchemaRegistryConfig
from domain.ports.schema_registry_port import SchemaType


class TestMessagingSDK:
    @pytest.fixture
    def mock_database(self):
        return Mock()

    @pytest.fixture
    def mock_schema_registry(self):
        return Mock()

    def test_initialization_empty(self):
        sdk = MessagingSDK()
        assert sdk._database is None
        assert sdk._schema_registry is None

    def test_initialization_with_database(self, mock_database):
        with patch('infrastructure.messaging.sdk.PostgresDatabaseAdapter', return_value=mock_database):
            config = DatabaseConfig(database_type="postgresql", connection_string="test")
            sdk = MessagingSDK(database_config=config)
            assert sdk._database is not None

    def test_initialization_with_schema_registry(self, mock_schema_registry):
        with patch('infrastructure.messaging.sdk.ConfluentSchemaRegistryAdapter', return_value=mock_schema_registry):
            config = SchemaRegistryConfig(url="http://localhost:8081")
            sdk = MessagingSDK(schema_registry_config=config)
            assert sdk._schema_registry is not None

    def test_configure_database_postgresql(self, mock_database):
        with patch('infrastructure.messaging.sdk.PostgresDatabaseAdapter', return_value=mock_database):
            sdk = MessagingSDK()
            config = DatabaseConfig(database_type="postgresql", connection_string="test")
            sdk.configure_database(config)
            assert sdk._database is not None

    def test_configure_database_mongodb(self, mock_database):
        with patch('infrastructure.messaging.sdk.MongoDatabaseAdapter', return_value=mock_database):
            sdk = MessagingSDK()
            config = DatabaseConfig(database_type="mongodb", connection_string="test")
            sdk.configure_database(config)
            assert sdk._database is not None

    def test_configure_database_invalid_type(self):
        sdk = MessagingSDK()
        config = DatabaseConfig(database_type="invalid", connection_string="test")
        with pytest.raises(ValueError, match="Unsupported database type"):
            sdk.configure_database(config)

    def test_configure_schema_registry(self, mock_schema_registry):
        with patch('infrastructure.messaging.sdk.ConfluentSchemaRegistryAdapter', return_value=mock_schema_registry):
            sdk = MessagingSDK()
            config = SchemaRegistryConfig(url="http://localhost:8081")
            sdk.configure_schema_registry(config)
            assert sdk._schema_registry is not None

    def test_database_property_not_configured(self):
        sdk = MessagingSDK()
        with pytest.raises(RuntimeError, match="Database not configured"):
            _ = sdk.database

    def test_schema_registry_property_not_configured(self):
        sdk = MessagingSDK()
        with pytest.raises(RuntimeError, match="Schema Registry not configured"):
            _ = sdk.schema_registry

    def test_event_handler_property_not_configured(self):
        sdk = MessagingSDK()
        with pytest.raises(RuntimeError, match="Event handler not available"):
            _ = sdk.event_handler

    def test_schema_aware_handler_property_not_configured(self):
        sdk = MessagingSDK()
        with pytest.raises(RuntimeError, match="Schema-aware handler not available"):
            _ = sdk.schema_aware_handler

    def test_close(self, mock_database, mock_schema_registry):
        sdk = MessagingSDK()
        sdk._database = mock_database
        sdk._schema_registry = mock_schema_registry
        sdk.close()
        mock_database.close.assert_called_once()
        mock_schema_registry.close.assert_called_once()

    def test_context_manager(self, mock_database, mock_schema_registry):
        with patch('infrastructure.messaging.sdk.PostgresDatabaseAdapter', return_value=mock_database):
            with patch('infrastructure.messaging.sdk.ConfluentSchemaRegistryAdapter', return_value=mock_schema_registry):
                db_config = DatabaseConfig(database_type="postgresql", connection_string="test")
                schema_config = SchemaRegistryConfig(url="http://localhost:8081")
                
                with MessagingSDK(database_config=db_config, schema_registry_config=schema_config) as sdk:
                    assert sdk is not None
                mock_database.close.assert_called_once()


class TestFactoryFunctions:
    @patch('infrastructure.messaging.sdk.PostgresDatabaseAdapter')
    @patch('infrastructure.messaging.sdk.MessagingSDK')
    def test_create_postgres_sdk(self, mock_sdk, mock_adapter):
        result = create_postgres_sdk("test-dsn")
        assert result is not None
        mock_sdk.assert_called_once()

    @patch('infrastructure.messaging.sdk.MongoDatabaseAdapter')
    @patch('infrastructure.messaging.sdk.MessagingSDK')
    def test_create_mongodb_sdk(self, mock_sdk, mock_adapter):
        result = create_mongodb_sdk("test-uri")
        assert result is not None
        mock_sdk.assert_called_once()

    @patch('infrastructure.messaging.sdk.ConfluentSchemaRegistryAdapter')
    @patch('infrastructure.messaging.sdk.MessagingSDK')
    def test_create_schema_registry_sdk(self, mock_sdk, mock_adapter):
        result = create_schema_registry_sdk("http://localhost:8081")
        assert result is not None
        mock_sdk.assert_called_once()
