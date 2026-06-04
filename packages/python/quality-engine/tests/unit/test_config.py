from __future__ import annotations
from worker.config import load_config


def test_load_config_defaults():
    cfg = load_config({})
    assert cfg.kafka_consumer_group == "quality-engine-group"
    assert cfg.kafka_topic_input == "llm.spans.sampled"
    assert cfg.kafka_topic_scores == "llm.quality.scores"
    assert cfg.kafka_topic_toxicity == "llm.toxicity.flagged"
    assert cfg.kafka_topic_alerts == "alerts.quality.degradation"


def test_load_config_from_env():
    cfg = load_config({
        "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
        "KAFKA_CONSUMER_GROUP": "test-group",
        "REDIS_URL": "redis://redis:6379/1",
        "TEMPORAL_HOST": "temporal:7233",
        "CONSUMER_CONCURRENCY": "8",
    })
    assert cfg.kafka_bootstrap_servers == "kafka:9092"
    assert cfg.kafka_consumer_group == "test-group"
    assert cfg.redis_url == "redis://redis:6379/1"
    assert cfg.temporal_host == "temporal:7233"
    assert cfg.consumer_concurrency == 8
