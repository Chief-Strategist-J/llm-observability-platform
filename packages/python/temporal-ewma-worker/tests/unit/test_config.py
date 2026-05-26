import pytest
from worker.config import load_config
from shared.errors.base import ValidationError


def test_config_defaults() -> None:
    cfg = load_config({})
    assert cfg.temporal_host == "localhost:7239"
    assert cfg.clickhouse_port == 8129
    assert cfg.redis_url == "redis://localhost:6389/0"


def test_config_invalid_port() -> None:
    with pytest.raises(ValidationError):
        load_config({"CLICKHOUSE_PORT": "abc"})
