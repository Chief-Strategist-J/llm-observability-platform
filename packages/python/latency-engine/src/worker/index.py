from __future__ import annotations
import asyncio
import logging
import os
import signal
import json
import redis
from confluent_kafka import Consumer, KafkaError
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.opentelemetry import TracingInterceptor

from config import load_config
from handlers.latency_handler import LatencyHandler
from worker.workflows import LatencyBaselineWorkflow
from worker.activities import LatencyBaselineActivities
from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.kafka.confluent_producer_adapter import ConfluentKafkaProducerAdapter
from shared.tracing.tracer import init_tracer

logger = logging.getLogger(__name__)


async def run() -> None:
    init_tracer()
    cfg = load_config()

    # ── Shared adapters ───────────────────────────────────────────────────────
    from infra.adapters.metrics.prometheus_adapter import PrometheusMetricsAdapter
    metrics_adapter = PrometheusMetricsAdapter()
    redis_client = redis.from_url(cfg.redis_url)

    # ── Kafka consumer handler (event-driven — DDSketch + SLO) ───────────────
    handler = LatencyHandler(redis_client, cfg.slo_config_path, metrics=metrics_adapter)

    consumer = Consumer({
        "bootstrap.servers": cfg.kafka_bootstrap_servers,
        "group.id": cfg.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,  # manual commit to control batches
    })
    consumer.subscribe([cfg.kafka_topic_input])
    logger.info(
        "latency-engine consumer started on topic=%s group=%s",
        cfg.kafka_topic_input, cfg.kafka_consumer_group,
    )

    # ── Temporal baseline scheduler adapters ─────────────────────────────────
    clickhouse = ClickHouseAdapter(
        host=cfg.clickhouse_host,
        port=cfg.clickhouse_port,
        username=cfg.clickhouse_username,
        password=cfg.clickhouse_password,
        database=cfg.clickhouse_database,
    )
    redis_adapter = RedisAdapter(url=cfg.redis_url)
    kafka_producer = ConfluentKafkaProducerAdapter(
        bootstrap_servers=cfg.kafka_bootstrap_servers
    )
    baseline_activities = LatencyBaselineActivities(
        clickhouse=clickhouse,
        redis=redis_adapter,
        kafka=kafka_producer,
    )

    # ── Temporal client ───────────────────────────────────────────────────────
    temporal_client: Client | None = None
    if cfg.temporal_host:
        try:
            temporal_client = await Client.connect(
                cfg.temporal_host,
                namespace=cfg.temporal_namespace,
                interceptors=[TracingInterceptor()],
            )
            logger.info("Temporal client connected to %s", cfg.temporal_host)
        except Exception as exc:
            logger.warning("Could not connect to Temporal (%s) — baseline scheduler will not start.", exc)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, stop.set)
    loop.add_signal_handler(signal.SIGINT, stop.set)

    # ── Health API server ─────────────────────────────────────────────────────
    import uvicorn
    from api.rest.v1.app import app
    server_config = uvicorn.Config(app, host="0.0.0.0", port=cfg.health_port, log_level="info")
    server = uvicorn.Server(server_config)

    # ── Coroutine: Kafka span consumer loop ───────────────────────────────────
    async def consume() -> None:
        try:
            while not stop.is_set():
                spans_batch = []
                kafka_messages = []

                for _ in range(500):
                    msg = await loop.run_in_executor(None, lambda: consumer.poll(timeout=0.1))
                    if msg is None:
                        break
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        logger.error("Kafka error: %s", msg.error())
                        continue

                    kafka_messages.append(msg)
                    try:
                        payload = json.loads(msg.value().decode("utf-8"))
                        headers = msg.headers()
                        if headers:
                            for key, val in headers:
                                if key == "traceparent":
                                    payload["_traceparent"] = val.decode("utf-8") if isinstance(val, bytes) else val
                                elif key == "tracestate":
                                    payload["_tracestate"] = val.decode("utf-8") if isinstance(val, bytes) else val
                        spans_batch.append(payload)
                    except Exception as e:
                        logger.error("Failed to parse span JSON: %s", e)

                if spans_batch:
                    try:
                        handler.handle_spans(spans_batch)
                    except Exception as e:
                        logger.error("Failed to process span batch: %s", e)
                    try:
                        await loop.run_in_executor(None, lambda: consumer.commit(asynchronous=False))
                    except Exception as e:
                        logger.error("Failed to commit Kafka offset: %s", e)
                else:
                    await asyncio.sleep(0.05)
        finally:
            consumer.close()
            logger.info("latency-engine consumer closed")

    # ── Coroutine: Temporal baseline worker ───────────────────────────────────
    async def run_temporal_worker() -> None:
        if temporal_client is None:
            logger.warning("Temporal unavailable — latency baseline scheduler will not start.")
            return
        worker = Worker(
            temporal_client,
            task_queue=cfg.temporal_task_queue,
            workflows=[LatencyBaselineWorkflow],
            activities=[baseline_activities.hourly_checkpoint],
            interceptors=[TracingInterceptor()],
        )
        logger.info("latency-engine temporal baseline worker started queue=%s", cfg.temporal_task_queue)
        await worker.run()

    await asyncio.gather(
        consume(),
        run_temporal_worker(),
        server.serve(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
