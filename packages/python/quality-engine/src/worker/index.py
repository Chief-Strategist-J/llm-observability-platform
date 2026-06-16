from __future__ import annotations
import asyncio
import logging
import os
import signal

from confluent_kafka import Consumer, KafkaError  # type: ignore[import-untyped]
from opentelemetry import trace
from opentelemetry.propagate import extract as otel_extract
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
    from shared.tracing.tracer import configure_tracer
    configure_tracer("quality-engine")

    cfg = load_config()


    # Wire adapters (dependency injection)
    repo     = PostgresQualityScoreAdapter(dsn=cfg.postgres_dsn)
    cache    = RedisBaselineCacheAdapter(url=cfg.redis_url)
    embedder = HttpEmbeddingClientAdapter(base_url=cfg.embedding_worker_url)
    producer = ConfluentKafkaProducerAdapter(bootstrap_servers=cfg.kafka_bootstrap_servers)

    if cfg.temporal_host:
        temporal_client = await Client.connect(cfg.temporal_host, namespace=cfg.temporal_namespace)
        temporal        = TemporalClientAdapter(client=temporal_client, task_queue=cfg.temporal_task_queue)
    else:
        logger.warning("TEMPORAL_HOST is not set — running without Temporal (local/dev mode)")
        temporal = TemporalClientAdapter(client=None, task_queue=cfg.temporal_task_queue)  # type: ignore[arg-type]

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
    consumer.subscribe([cfg.kafka_topic_input, cfg.kafka_topic_scores])
    logger.info(
        "quality-engine consumer started topics=%s,%s group=%s",
        cfg.kafka_topic_input, cfg.kafka_topic_scores, cfg.kafka_consumer_group,
    )

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, stop.set)
    loop.add_signal_handler(signal.SIGINT, stop.set)

    import uvicorn
    from api.rest.v1.app import app
    server_config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(server_config)

    async def consume() -> None:
        try:
            while not stop.is_set():
                msg = await loop.run_in_executor(None, lambda: consumer.poll(timeout=0.2))
                if msg is None:
                    await asyncio.sleep(0.05)
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
                        "worker.queue_name": msg.topic(),
                        "worker.consumer_group": cfg.kafka_consumer_group,
                        "deployment.env": _DEPLOYMENT_ENV,
                        "messaging.system": "kafka",
                        "messaging.destination": msg.topic(),
                        "messaging.kafka.partition": str(msg.partition()),
                        "messaging.kafka.offset": str(msg.offset()),
                    },
                ):
                    # Retry loop with dead-letter fallback
                    last_exc: Exception | None = None
                    for attempt in range(1, _MAX_RETRIES + 1):
                        try:
                            if msg.topic() == cfg.kafka_topic_input:
                                await handler.handle(msg.value(), headers)
                            else:
                                import json
                                from datetime import datetime, timezone
                                from handlers.span_quality.types import ScoreMap
                                val = json.loads(msg.value())
                                scores_raw = val.get("scores", {})
                                scores = ScoreMap(
                                    coherence=scores_raw.get("coherence"),
                                    toxicity=scores_raw.get("toxicity"),
                                    faithfulness=scores_raw.get("faithfulness"),
                                    perplexity=scores_raw.get("perplexity"),
                                )
                                # scored_at string to datetime
                                scored_at_str = val.get("scored_at")
                                if scored_at_str:
                                    scored_at = datetime.fromisoformat(scored_at_str)
                                else:
                                    scored_at = datetime.now(timezone.utc)
                                await handler.handle_score_result(
                                    span_id=val["span_id"],
                                    model=val["model"],
                                    endpoint=val["endpoint"],
                                    prompt_type=val["prompt_type"],
                                    response_language=val["response_language"],
                                    scores=scores,
                                    quality_flags=val.get("quality_flags", []),
                                    scored_at=scored_at,
                                    trace_id=val["trace_id"],
                                    user_id=val.get("user_id"),
                                )
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

    await asyncio.gather(
        consume(),
        server.serve(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
