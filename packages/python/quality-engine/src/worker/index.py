from __future__ import annotations
import asyncio
import json
import logging
import os
import signal

from confluent_kafka import Consumer, KafkaError  # type: ignore[import-untyped]
from opentelemetry import trace
from opentelemetry.propagate import extract as otel_extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from temporalio.client import Client

from worker.config import load_config
from handlers.span_quality.handler import SpanQualityHandler
from infra.adapters.postgres.postgres_adapter import PostgresQualityScoreAdapter
from infra.adapters.redis.redis_adapter import RedisBaselineCacheAdapter
from infra.adapters.embedding.http_embedding_adapter import HttpEmbeddingClientAdapter
from infra.adapters.kafka.confluent_producer_adapter import ConfluentKafkaProducerAdapter
from infra.adapters.temporal.temporal_client_adapter import TemporalClientAdapter

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("quality-engine.worker")

_MAX_RETRIES = 3
_DEAD_LETTER_TOPIC = "llm.spans.sampled.dlq"
_DEPLOYMENT_ENV = os.environ.get("DEPLOYMENT_ENV", "local")


async def run() -> None:
    cfg = load_config()

    # Wire adapters (dependency injection)
    repo     = PostgresQualityScoreAdapter(dsn=cfg.postgres_dsn)
    cache    = RedisBaselineCacheAdapter(url=cfg.redis_url)
    embedder = HttpEmbeddingClientAdapter(base_url=cfg.embedding_worker_url)
    producer = ConfluentKafkaProducerAdapter(bootstrap_servers=cfg.kafka_bootstrap_servers)

    temporal_client = await Client.connect(cfg.temporal_host, namespace=cfg.temporal_namespace)
    temporal        = TemporalClientAdapter(client=temporal_client, task_queue=cfg.temporal_task_queue)

    handler = SpanQualityHandler(
        repo=repo,
        cache=cache,
        temporal=temporal,
        embedding_client=embedder,
        producer=producer,
    )

    consumer = Consumer({
        "bootstrap.servers": cfg.kafka_bootstrap_servers,
        "group.id": cfg.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,  # manual offset commit after success
    })
    consumer.subscribe([cfg.kafka_topic_input])
    logger.info(
        "quality-engine consumer started topic=%s group=%s",
        cfg.kafka_topic_input, cfg.kafka_consumer_group,
    )

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, stop.set)
    loop.add_signal_handler(signal.SIGINT, stop.set)

    try:
        while not stop.is_set():
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("kafka_error code=%s reason=%s", msg.error().code(), msg.error().str())
                continue

            # W3C traceparent extraction from message headers — used as parent span context
            # Rule: tracing-rules-for-workers.md line 6
            headers: dict[str, str] = {}
            if msg.headers():
                headers = {k: v.decode() for k, v in msg.headers() if v}
            ctx = otel_extract(headers)

            # Root span per message — required by tracing-rules-for-workers.md lines 4 and 7
            # Carries: service.name, worker.type, worker.queue_name, deployment.env
            with tracer.start_as_current_span(
                "quality_engine.consumer.process",
                context=ctx,
                attributes={
                    "service.name": "quality-engine",
                    "worker.type": "event",
                    "worker.queue_name": cfg.kafka_topic_input,
                    "worker.consumer_group": cfg.kafka_consumer_group,
                    "deployment.env": _DEPLOYMENT_ENV,
                    "messaging.system": "kafka",
                    "messaging.destination": cfg.kafka_topic_input,
                    "messaging.kafka.partition": str(msg.partition()),
                    "messaging.kafka.offset": str(msg.offset()),
                },
            ):
                # Retry loop with dead-letter fallback
                last_exc: Exception | None = None
                for attempt in range(1, _MAX_RETRIES + 1):
                    try:
                        await handler.handle(msg.value(), headers)
                        last_exc = None
                        break
                    except Exception as exc:
                        last_exc = exc
                        logger.warning(
                            "handler_attempt_failed attempt=%s/%s offset=%s exc=%s",
                            attempt, _MAX_RETRIES, msg.offset(), exc,
                        )
                        await asyncio.sleep(0.2 * attempt)

                if last_exc is not None:
                    logger.error(
                        "handler_max_retries_exceeded — routing to DLQ offset=%s", msg.offset()
                    )
                    producer.produce(
                        topic=_DEAD_LETTER_TOPIC,
                        key=str(msg.offset()),
                        value=msg.value(),
                        headers=headers,
                    )

            # Commit offset only after successful processing or DLQ routing (outside span)
            consumer.commit(message=msg, asynchronous=False)

    finally:
        consumer.close()
        producer.flush()
        logger.info("quality-engine consumer shut down cleanly")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
