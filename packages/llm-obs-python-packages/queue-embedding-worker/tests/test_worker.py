import pytest

from worker.config import load_config
from worker.index import handle_job
from worker.registry import JOB_REGISTRY


def test_load_config_defaults():
    config = load_config({})
    assert config.account_id == "local-account"
    assert config.queue_name == "span-enrichment"
    assert config.embedding_dimensions == 1536
    assert config.embedding_provider == "cloudflare"


def test_load_config_from_env_values():
    config = load_config(
        {
            "CF_ACCOUNT_ID": "acct-123",
            "CF_QUEUE_NAME": "queue-x",
            "EMBEDDING_DIMENSIONS": "1024",
        }
    )
    assert config.account_id == "acct-123"
    assert config.queue_name == "queue-x"
    assert config.embedding_dimensions == 1024


def test_invalid_dimensions_raise_error():
    with pytest.raises(Exception, match="greater than zero"):
        load_config({"EMBEDDING_DIMENSIONS": "0"})


def test_handle_enrich_span_job():
    message = {
        "trace_id": "trace-1",
        "span_id": "span-2",
        "text": "hello world",
        "model": "text-embedding-3-small",
    }
    out = handle_job("enrich-span", message, env={"EMBEDDING_DIMENSIONS": "128"})
    assert out["trace_id"] == "trace-1"
    assert out["span_id"] == "span-2"
    assert out["model"] == "text-embedding-3-small"
    assert out["dimensions"] == 128
    assert out["embedding_key"].startswith("emb_")
    assert out["provider"] == "cloudflare"


def test_unknown_job_raises():
    with pytest.raises(KeyError, match="Unknown job"):
        handle_job("missing", {}, env={})


def test_registry_contains_enrich_span_handler():
    assert "enrich-span" in JOB_REGISTRY
    assert callable(JOB_REGISTRY["enrich-span"].handler)
