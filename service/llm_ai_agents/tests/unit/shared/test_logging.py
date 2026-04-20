import pytest
from unittest.mock import patch, MagicMock
from services.shared.logging import bootstrap_langsmith
import os


def test_does_nothing_when_no_api_key(monkeypatch):
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    bootstrap_langsmith()
    assert os.environ.get("LANGCHAIN_TRACING_V2") is None


def test_sets_tracing_env_vars_when_key_present(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_API_KEY", "test-key-123")
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.delenv("LANGCHAIN_PROJECT", raising=False)

    bootstrap_langsmith()

    assert os.environ.get("LANGCHAIN_API_KEY") == "test-key-123"
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_PROJECT") == "llm-observability-platform"


def test_does_not_override_existing_project(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_API_KEY", "key")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "my-custom-project")

    bootstrap_langsmith()

    assert os.environ.get("LANGCHAIN_PROJECT") == "my-custom-project"
