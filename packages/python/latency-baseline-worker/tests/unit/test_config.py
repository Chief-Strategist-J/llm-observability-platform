import pytest
from worker.config import load_config
from shared.errors.base import ValidationError

def test_load_config_default() -> None:
    cfg = load_config({})
    assert cfg.temporal_host == "localhost:7239"
    assert cfg.clickhouse_port == 8129

def test_load_config_env() -> None:
    cfg = load_config({
        "TEMPORAL_HOST": "test-host:1111",
        "CLICKHOUSE_PORT": "1234",
    })
    assert cfg.temporal_host == "test-host:1111"
    assert cfg.clickhouse_port == 1234

def test_load_config_invalid_int() -> None:
    with pytest.raises(ValidationError):
        load_config({"CLICKHOUSE_PORT": "abc"})
