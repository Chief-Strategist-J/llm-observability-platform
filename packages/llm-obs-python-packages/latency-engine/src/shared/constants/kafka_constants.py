from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class KafkaConstants:
    BOOTSTRAP_SERVERS_KEY: str = "bootstrap.servers"
    KAFKA_BROKER_ALIAS: str = "llmobs-kafka-broker"
    LOCAL_HOSTNAMES: tuple[str, ...] = ("localhost", "127.0.0.1")
    DEFAULT_FLUSH_TIMEOUT_SEC: float = 10.0
    DEFAULT_RAW_TOPIC: str = "llm.spans.raw"
    DEFAULT_DLQ_TOPIC: str = "llm.spans.dlq"
    HEADER_TRACEPARENT: str = "traceparent"
    HEADER_X_TRACE_ID: str = "x-trace-id"

kafka_constants = KafkaConstants()
