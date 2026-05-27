import json
import logging
from datetime import datetime, timezone
from typing import Any
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import redis as redis_lib
import yaml
from confluent_kafka import Consumer, Producer, KafkaError
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context

from handlers.llm_spans_raw.index import (
    process_batch,
    FENWICK_UPDATE_LUA,
    TOKEN_BUCKET_DEDUCT_LUA,
    DEDUP_CHECK_LUA,
    DEDUP_TTL_SECONDS,
)
from handlers.llm_spans_raw.types import RawSpanEvent, FenwickUpdate
from shared.types.cost_types import PriceEntry, ProcessingError
from shared.utils.retry import with_retry
from worker.config import load_config
from worker.registry import build_registry

logger = logging.getLogger(__name__)

SERVICE_NAME = "event-cost-worker"
tracer = trace.get_tracer(SERVICE_NAME)


def _init_tracing() -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


class RedisFenwickAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(FENWICK_UPDATE_LUA)

    def pipeline_update(self, updates: list[FenwickUpdate]) -> None:
        pipe = self._client.pipeline(transaction=False)
        for u in updates:
            redis_key = f"fenwick:{u.dimension}:{u.window}:{u.key}"
            n = 1024
            i = 1
            pipe.evalsha(
                self._script.sha,
                1,
                redis_key,
                str(u.delta),
                str(i),
                str(n),
            )
        pipe.execute()


class RedisTokenBucketAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(TOKEN_BUCKET_DEDUCT_LUA)

    def deduct(self, bucket_key: str, delta: int) -> int:
        result = self._script(keys=[bucket_key], args=[str(delta)])
        return int(result)


class RedisEwmaReaderAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client

    def get_ewma(self, service: str, model: str, hour_of_week: int) -> float | None:
        key = f"ewma:cost:{service}:{model}:{hour_of_week}"
        val = self._client.get(key)
        if val is not None:
            if isinstance(val, (str, bytes)):
                return float(val)
        return None


class RedisDedupAdapter:
    def __init__(self, client: redis_lib.Redis) -> None:
        self._client = client
        self._script = self._client.register_script(DEDUP_CHECK_LUA)

    def is_new(self, span_id: str) -> bool:
        result = self._script(
            keys=["dedup:cost_engine"],
            args=[span_id, str(DEDUP_TTL_SECONDS)],
        )
        return int(result) == 1


class YamlPriceLookupAdapter:
    def __init__(self, path: str) -> None:
        self._prices: dict[tuple[str, str, str], PriceEntry] = {}
        self._load(path)

    def _load(self, path: str) -> None:
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            for entry in data.get("prices", []):
                pe = PriceEntry(
                    model=entry["model"],
                    provider=entry["provider"],
                    input_price_per_token_micro=entry["input_price_per_token_micro"],
                    output_price_per_token_micro=entry["output_price_per_token_micro"],
                    version=entry["version"],
                )
                self._prices[(pe.model, pe.provider, pe.version)] = pe
        except FileNotFoundError:
            logger.warning("price config not found at %s", path)

    def get_price(self, model: str, provider: str, version: str) -> PriceEntry | None:
        return self._prices.get((model, provider, version))


def _extract_traceparent(headers: list[tuple[str, bytes]] | None) -> Context | None:
    if not headers:
        return None
    carrier: dict[str, str] = {}
    for key, value in headers:
        if key == "traceparent":
            carrier["traceparent"] = value.decode("utf-8") if isinstance(value, bytes) else value
        if key == "tracestate":
            carrier["tracestate"] = value.decode("utf-8") if isinstance(value, bytes) else value
    if not carrier:
        return None
    propagator = TraceContextTextMapPropagator()
    return propagator.extract(carrier)


def _deserialize_span(raw: bytes) -> RawSpanEvent:
    data: dict[str, Any] = json.loads(raw)
    return RawSpanEvent(
        span_id=data["span_id"],
        trace_id=data.get("trace_id", ""),
        service_name=data["service_name"],
        model=data["model"],
        provider=data["provider"],
        prompt_tokens=data["prompt_tokens"],
        completion_tokens=data["completion_tokens"],
        cost_usd_micro=data["cost_usd_micro"],
        price_version=data["price_version"],
        timestamp_utc=datetime.fromisoformat(data["timestamp_utc"]),
        user_id=data.get("user_id", ""),
        org_id=data.get("org_id", ""),
        project_id=data.get("project_id", ""),
        estimated_tokens=data.get("estimated_tokens", 0),
        raw_bytes=raw,
    )


def _run_consumer_loop(
    consumer: Consumer,
    dlq_producer: Producer,
    fenwick: RedisFenwickAdapter,
    bucket: RedisTokenBucketAdapter,
    ewma: RedisEwmaReaderAdapter,
    price_lookup: YamlPriceLookupAdapter,
    dedup: RedisDedupAdapter,
    config: Any,
) -> None:
    dlq_total = 0
    while True:
        messages = consumer.consume(
            num_messages=config.batch_size,
            timeout=config.poll_timeout_s,
        )
        if not messages:
            continue

        spans: list[RawSpanEvent] = []
        for msg in messages:
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("kafka error: %s", msg.error())
                continue

            parent_ctx = _extract_traceparent(msg.headers())

            with tracer.start_as_current_span(
                "cost_engine.process_message",
                context=parent_ctx,
                attributes={
                    "service.name": SERVICE_NAME,
                    "messaging.system": "kafka",
                    "messaging.destination": config.kafka_topic,
                },
            ):
                try:
                    span = _deserialize_span(msg.value())
                    spans.append(span)
                except Exception:
                    logger.exception("deserialization failed")
                    dlq_producer.produce(
                        config.kafka_dlq_topic,
                        value=msg.value(),
                    )
                    dlq_producer.flush()
                    dlq_total += 1

        if not spans:
            consumer.commit(asynchronous=False)
            continue

        failed_spans: list[RawSpanEvent] = []

        for span in spans:
            try:
                def _process(s=span) -> None:
                    process_batch(
                        [s], fenwick, bucket, ewma, price_lookup, dedup
                    )

                with_retry(
                    _process,
                    max_retries=config.max_retries,
                    base_ms=config.retry_base_ms,
                )
            except ProcessingError:
                logger.exception("span sent to DLQ span_id=%s", span.span_id)
                failed_spans.append(span)

        for span in failed_spans:
            dlq_producer.produce(
                config.kafka_dlq_topic,
                value=span.raw_bytes,
            )
            dlq_total += 1
        if failed_spans:
            dlq_producer.flush()

        consumer.commit(asynchronous=False)
        logger.info(
            "batch committed spans=%d dlq_total=%d",
            len(spans),
            dlq_total,
        )


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


def _start_health_server(port: int = 8001) -> None:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main() -> None:
    _init_tracing()
    config = load_config()
    _start_health_server()

    redis_client = redis_lib.from_url(config.redis_url)
    fenwick = RedisFenwickAdapter(redis_client)
    bucket = RedisTokenBucketAdapter(redis_client)
    ewma = RedisEwmaReaderAdapter(redis_client)
    dedup = RedisDedupAdapter(redis_client)
    price_lookup = YamlPriceLookupAdapter(config.price_config_path)

    build_registry(
        batch_handler=lambda spans: process_batch(
            spans, fenwick, bucket, ewma, price_lookup, dedup
        )
    )

    consumer = Consumer({
        "bootstrap.servers": config.kafka_bootstrap_servers,
        "group.id": config.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([config.kafka_topic])

    dlq_producer = Producer({
        "bootstrap.servers": config.kafka_bootstrap_servers,
    })

    logger.info("event-cost-worker started, consuming %s", config.kafka_topic)

    try:
        _run_consumer_loop(
            consumer, dlq_producer, fenwick, bucket, ewma, price_lookup, dedup, config
        )
    finally:
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
