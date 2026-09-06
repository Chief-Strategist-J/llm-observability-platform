import pytest

from worker.config import load_config
from shared.errors.base import ValidationError


def test_defaults_load():
    cfg = load_config({})
    assert cfg.queue_name == "span-enrichment"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("EMBEDDING_DIMENSIONS", "0"),
        ("WORKER_CONCURRENCY", "0"),
        ("WORKER_RATE_LIMIT_PER_SEC", "0"),
        ("WORKER_BACKOFF_MS", "0"),
        ("EMBEDDING_DIMENSIONS", "-1"),
        ("WORKER_CONCURRENCY", "-1"),
        ("WORKER_RATE_LIMIT_PER_SEC", "-1"),
        ("WORKER_BACKOFF_MS", "-1"),
        ("EMBEDDING_DIMENSIONS", "abc"),
        ("WORKER_CONCURRENCY", "x"),
        ("WORKER_RATE_LIMIT_PER_SEC", "1.2"),
        ("WORKER_BACKOFF_MS", " "),
    ],
)
def test_invalid_positive_int_values(key, value):
    with pytest.raises(ValidationError):
        load_config({key: value})


@pytest.mark.parametrize(
    "env",
    [
        {"EMBEDDING_DIMENSIONS": "1", "WORKER_CONCURRENCY": "1", "WORKER_RATE_LIMIT_PER_SEC": "1", "WORKER_BACKOFF_MS": "1"},
        {"EMBEDDING_DIMENSIONS": "1536", "WORKER_CONCURRENCY": "5", "WORKER_RATE_LIMIT_PER_SEC": "50", "WORKER_BACKOFF_MS": "500"},
        {"EMBEDDING_DIMENSIONS": "4096", "WORKER_CONCURRENCY": "32", "WORKER_RATE_LIMIT_PER_SEC": "1000", "WORKER_BACKOFF_MS": "2500"},
    ],
)
def test_valid_positive_int_values(env):
    cfg = load_config(env)
    assert cfg.embedding_dimensions > 0
    assert cfg.concurrency > 0
    assert cfg.rate_limit_per_sec > 0
    assert cfg.backoff_ms > 0
