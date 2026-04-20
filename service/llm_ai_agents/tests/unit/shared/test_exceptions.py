import pytest
from services.shared.exceptions import (
    ProviderNotFoundError,
    RAGIngestionError,
    AgentExecutionError,
    ConfigNotFoundError,
    CollectionNotFoundError,
)


def test_provider_not_found_is_exception():
    with pytest.raises(ProviderNotFoundError):
        raise ProviderNotFoundError("unknown-provider")


def test_rag_ingestion_error_carries_message():
    exc = RAGIngestionError("failed to load url")
    assert "failed to load url" in str(exc)


def test_agent_execution_error_is_exception():
    with pytest.raises(AgentExecutionError):
        raise AgentExecutionError("agent crashed")


def test_config_not_found_carries_path():
    exc = ConfigNotFoundError("/some/path/config.yaml")
    assert "/some/path/config.yaml" in str(exc)


def test_collection_not_found_is_exception():
    with pytest.raises(CollectionNotFoundError):
        raise CollectionNotFoundError("my-collection")


def test_all_exceptions_are_subclasses_of_exception():
    for cls in [
        ProviderNotFoundError,
        RAGIngestionError,
        AgentExecutionError,
        ConfigNotFoundError,
        CollectionNotFoundError,
    ]:
        assert issubclass(cls, Exception)
