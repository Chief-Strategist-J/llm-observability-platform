import os
import time
import uuid
from datetime import datetime, timezone
from confluent_kafka import Consumer, KafkaError
from src.infra.adapters.kafka.reliable_adapter import ReliableKafkaSpanReporter

def test_reliable_reporter_real_kafka_integration():
    import socket
    import pytest
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(("localhost", 9094))
        s.close()
    except Exception:
        pytest.skip("Kafka is not running on localhost:9094")

    wal_db = "/tmp/llm-obs-wal-integration.db"
    if os.path.exists(wal_db):
        try:
            os.remove(wal_db)
        except OSError:
            pass

    topic = "llm.spans.raw"
    bootstrap_servers = "localhost:9094"

    reporter = ReliableKafkaSpanReporter(
        bootstrap_servers=bootstrap_servers,
        topic=topic,
        wal_path=wal_db,
        max_buffer_size=10
    )

    span_id = str(uuid.uuid4())
    span_data = {
        "span_id": span_id,
        "trace_id": str(uuid.uuid4()),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "integration-test-service",
        "endpoint": "/v1/chat/completions",
        "environment": "production",
        "prompt_tokens": 150,
        "completion_tokens": 50,
        "latency_ms_total": 450,
        "finish_reason": "stop",
        "cost_usd_micro": 300,
        "price_version": "v1",
        "token_count_method": "tiktoken",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

    reporter.report(span_data)

    consumer_config = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": f"integration-test-group-{uuid.uuid4()}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])

    found = False
    start_time = time.time()
    while time.time() - start_time < 10.0:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                break

        try:
            val_bytes = msg.value()
            if val_bytes:
                from src.infra.clients.v1.llm.observability.v1.span_pb2 import LLMSpan
                proto_span = LLMSpan()
                proto_span.ParseFromString(val_bytes)
                if proto_span.span_id == span_id:
                    found = True
                    break
        except Exception:
            pass

    consumer.close()
    reporter.close()

    if os.path.exists(wal_db):
        try:
            os.remove(wal_db)
        except OSError:
            pass

    assert found is True
