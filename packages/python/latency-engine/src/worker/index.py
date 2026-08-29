from __future__ import annotations
import asyncio
import logging
import signal
import json
import socket
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
from infra.adapters.metrics.prometheus_adapter import PrometheusMetricsAdapter
from infra.messaging.migrations.run_all_migrations import run_all_migrations

logger = logging.getLogger(__name__)

def is_socket_reachable(host_port: str, timeout: float = 0.2) -> bool:
    try:
        parts = host_port.split(",")[0].strip().split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 9092
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

async def run() -> None:
    init_tracer()
    cfg = load_config()

    try:
        run_all_migrations()
    except Exception as exc:
        logger.warning("Auto-migrations on startup encountered warning: %s", exc)

    metrics_adapter = PrometheusMetricsAdapter()
    redis_client = None
    try:
        redis_client = redis.from_url(cfg.redis_url)
    except Exception as exc:
        logger.warning("Could not connect to Redis (%s)", exc)

    handler = LatencyHandler(redis_client, cfg.slo_config_path, metrics=metrics_adapter) if redis_client else None

    consumer = None
    if is_socket_reachable(cfg.kafka_bootstrap_servers):
        try:
            consumer = Consumer({
                "bootstrap.servers": cfg.kafka_bootstrap_servers,
                "group.id": cfg.kafka_consumer_group,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
                "log_level": 2,
            })
            consumer.subscribe([cfg.kafka_topic_input])
            logger.info(
                "latency-engine consumer started on topic=%s group=%s",
                cfg.kafka_topic_input, cfg.kafka_consumer_group,
            )
        except Exception as exc:
            logger.warning("Could not start Kafka consumer (%s)", exc)
    else:
        logger.warning("Kafka broker unreachable at %s — skipping consumer thread to prevent log spam.", cfg.kafka_bootstrap_servers)

    baseline_activities = None
    ch_host_port = f"{cfg.clickhouse_host}:{cfg.clickhouse_port}"
    if is_socket_reachable(ch_host_port):
        try:
            clickhouse = ClickHouseAdapter(
                host=cfg.clickhouse_host,
                port=cfg.clickhouse_port,
                username=cfg.clickhouse_username,
                password=cfg.clickhouse_password,
                database=cfg.clickhouse_database,
            )
            redis_adapter = RedisAdapter(url=cfg.redis_url)
            kafka_producer = None
            if is_socket_reachable(cfg.kafka_bootstrap_servers):
                kafka_producer = ConfluentKafkaProducerAdapter(
                    bootstrap_servers=cfg.kafka_bootstrap_servers
                )
            baseline_activities = LatencyBaselineActivities(
                clickhouse=clickhouse,
                redis=redis_adapter,
                kafka=kafka_producer,
            )
        except Exception as exc:
            logger.warning("Could not initialize ClickHouse baseline adapters (%s)", exc)
    else:
        logger.warning("ClickHouse unreachable at %s — baseline scheduler disabled.", ch_host_port)

    temporal_client: Client | None = None
    if cfg.temporal_host and baseline_activities:
        if is_socket_reachable(cfg.temporal_host):
            try:
                temporal_client = await Client.connect(
                    cfg.temporal_host,
                    namespace=cfg.temporal_namespace,
                    interceptors=[TracingInterceptor()],
                )
                logger.info("Temporal client connected to %s", cfg.temporal_host)
            except Exception as exc:
                logger.warning("Could not connect to Temporal (%s)", exc)
        else:
            logger.warning("Temporal unreachable at %s", cfg.temporal_host)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    try:
        loop.add_signal_handler(signal.SIGTERM, stop.set)
        loop.add_signal_handler(signal.SIGINT, stop.set)
    except NotImplementedError:
        pass

    import uvicorn
    from api.rest.v1.app import app
    server_config = uvicorn.Config(app, host="0.0.0.0", port=cfg.health_port, log_level="info")
    server = uvicorn.Server(server_config)

    async def consume() -> None:
        if not consumer or not handler:
            return
        try:
            while not stop.is_set():
                spans_batch = []
                for _ in range(500):
                    msg = await loop.run_in_executor(None, lambda: consumer.poll(timeout=0.1))
                    if msg is None:
                        break
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        logger.error("Kafka error: %s", msg.error())
                        continue

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
            if consumer:
                consumer.close()

    async def run_temporal_worker() -> None:
        if temporal_client is None or baseline_activities is None:
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
