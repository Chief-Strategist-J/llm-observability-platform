from __future__ import annotations
import asyncio
import logging
import os
import signal
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
import redis
from confluent_kafka import Consumer, KafkaError

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from config import load_config
from handlers.latency_handler import LatencyHandler

logger = logging.getLogger(__name__)

def _init_tracing() -> None:
    res = Resource.create({
        "service.name": "latency-engine",
        "service.version": "0.1.0",
        "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
    })
    provider = TracerProvider(resource=res)
    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    if os.getenv("SKIP_OTLP_EXPORTER") != "true":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
        except ImportError:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
                provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            except ImportError:
                pass
    trace.set_tracer_provider(provider)

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass

def _start_health_server(port: int = 8002) -> None:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server started on port %s", port)

async def run() -> None:
    _init_tracing()
    cfg = load_config()
    
    # Start health server
    health_port = int(os.getenv("HEALTH_PORT", "8002"))
    _start_health_server(health_port)
    
    # Initialize redis and handler
    redis_client = redis.from_url(cfg.redis_url)
    handler = LatencyHandler(redis_client, cfg.slo_config_path)

    consumer = Consumer({
        "bootstrap.servers": cfg.kafka_bootstrap_servers,
        "group.id": cfg.kafka_consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False, # manual commit to control batches
    })
    
    consumer.subscribe([cfg.kafka_topic_input])
    logger.info("latency-engine consumer started on topic=%s group=%s", cfg.kafka_topic_input, cfg.kafka_consumer_group)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, stop.set)
    loop.add_signal_handler(signal.SIGINT, stop.set)

    # Poll and process loop
    try:
        while not stop.is_set():
            # Batch: process 500 spans per Kafka poll
            spans_batch = []
            kafka_messages = []
            
            # Read messages until we hit 500 or timeout
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
                    payload = json.loads(msg.value().decode('utf-8'))
                    
                    # Extract traceparent context from Kafka headers and add to payload
                    headers = msg.headers()
                    if headers:
                        for key, val in headers:
                            if key == "traceparent":
                                payload["_traceparent"] = val.decode('utf-8') if isinstance(val, bytes) else val
                            elif key == "tracestate":
                                payload["_tracestate"] = val.decode('utf-8') if isinstance(val, bytes) else val
                                
                    spans_batch.append(payload)
                except Exception as e:
                    logger.error("Failed to parse span JSON: %s", e)

            if spans_batch:
                try:
                    handler.handle_spans(spans_batch)
                except Exception as e:
                    logger.error("Failed to process span batch: %s", e)
                
                # Manual commit of offset after handling batch
                # Commit Kafka offset even during Redis outage (don't block Kafka progress) (F-L-06)
                try:
                    await loop.run_in_executor(None, lambda: consumer.commit(asynchronous=False))
                except Exception as e:
                    logger.error("Failed to commit Kafka offset: %s", e)
            else:
                await asyncio.sleep(0.05)
                
    finally:
        consumer.close()
        logger.info("latency-engine consumer closed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())

