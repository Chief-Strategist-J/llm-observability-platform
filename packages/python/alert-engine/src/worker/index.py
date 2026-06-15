import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from confluent_kafka import Consumer, KafkaError
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from prometheus_client import start_http_server

from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context import Context

from worker.config import load_config
from worker.registry import build_registry
from infra.adapters.postgres.postgres_adapter import PostgresAdapter
from infra.adapters.redis.redis_adapter import RedisAdapter
from infra.adapters.slack.slack_adapter import SlackAdapter
from infra.adapters.pagerduty.pagerduty_adapter import PagerDutyAdapter
from infra.adapters.metrics.prometheus_adapter import PrometheusAdapter
from handlers.alerts_budget.handler import BudgetAlertHandler
from handlers.alerts_cost_anomaly.handler import CostAnomalyAlertHandler
from handlers.alerts_toxicity.handler import ToxicityAlertHandler
from handlers.alerts_quality_degradation.handler import QualityDegradationAlertHandler


logger = logging.getLogger(__name__)

SERVICE_NAME = "alert-engine"
tracer = trace.get_tracer(SERVICE_NAME)

def _init_tracing() -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

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

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass

def _start_health_server(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

def main() -> None:
    _init_tracing()
    config = load_config()
    _start_health_server(config.health_check_port)
    
    try:
        start_http_server(config.prometheus_metrics_port)
    except OSError:
        pass

    postgres_adapter = PostgresAdapter(config.postgres_dsn)
    redis_adapter = RedisAdapter(config.redis_url)
    slack_adapter = SlackAdapter(config.slack_webhook_url)
    pagerduty_adapter = PagerDutyAdapter(config.pagerduty_routing_key)
    metrics_adapter = PrometheusAdapter()

    budget_handler = BudgetAlertHandler(
        db_port=postgres_adapter,
        redis_port=redis_adapter,
        slack_port=slack_adapter,
        metrics_port=metrics_adapter,
        service_owners_path=config.service_owners_file_path
    )

    cost_anomaly_handler = CostAnomalyAlertHandler(
        db_port=postgres_adapter,
        redis_port=redis_adapter,
        slack_port=slack_adapter,
        pagerduty_port=pagerduty_adapter,
        metrics_port=metrics_adapter
    )

    toxicity_handler = ToxicityAlertHandler(
        redis_port=redis_adapter,
        slack_port=slack_adapter
    )

    degradation_handler = QualityDegradationAlertHandler(
        redis_port=redis_adapter,
        slack_port=slack_adapter
    )

    handlers_registry = build_registry(
        budget_handler=budget_handler.handle,
        cost_anomaly_handler=cost_anomaly_handler.handle,
        toxicity_handler=toxicity_handler.handle,
        degradation_handler=degradation_handler.handle
    )


    consumer = Consumer({
        "bootstrap.servers": config.kafka_bootstrap_servers,
        "group.id": config.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe(config.kafka_topics)

    logger.info("alert-engine worker started, consuming %s", config.kafka_topics)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka error: %s", msg.error())
                continue

            topic = msg.topic()
            handler_def = handlers_registry.get(topic)
            if not handler_def:
                consumer.commit(message=msg, asynchronous=False)
                continue

            parent_ctx = _extract_traceparent(msg.headers())

            with tracer.start_as_current_span(
                "alert_engine.process_message",
                context=parent_ctx,
                attributes={
                    "service.name": SERVICE_NAME,
                    "messaging.system": "kafka",
                    "messaging.destination": topic,
                },
            ):
                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                    handler_def.handler(payload)
                except Exception:
                    logger.exception("Failed to process message on topic %s", topic)

            consumer.commit(message=msg, asynchronous=False)

    finally:
        consumer.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
