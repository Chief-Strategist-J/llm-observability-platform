from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class LatencyEngineConfig:
    kafka_bootstrap_servers: str
    kafka_consumer_group: str
    kafka_topic_input: str
    redis_url: str
    slo_config_path: str

def load_config(env: dict[str, str] | None = None) -> LatencyEngineConfig:
    source = env or os.environ
    return LatencyEngineConfig(
        kafka_bootstrap_servers = source.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_consumer_group    = source.get("KAFKA_CONSUMER_GROUP", "latency-engine-cg"),
        kafka_topic_input       = source.get("KAFKA_TOPIC_INPUT", "llm.spans.raw"),
        redis_url               = source.get("REDIS_URL", "redis://localhost:6379/0"),
        slo_config_path         = source.get("SLO_CONFIG_PATH", "src/slo_config.yaml"),
    )
