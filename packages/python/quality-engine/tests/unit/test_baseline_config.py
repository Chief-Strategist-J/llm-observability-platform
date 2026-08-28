import os
from worker.config import load_config

def test_load_config_defaults() -> None:
    cfg = load_config({})
    assert cfg.temporal_host == "localhost:7239"
    assert cfg.temporal_namespace == "default"
    assert cfg.temporal_task_queue == "quality-baseline-tasks"
    assert cfg.clickhouse_host == "localhost"
    assert cfg.redis_url == "redis://localhost:6389/0"
