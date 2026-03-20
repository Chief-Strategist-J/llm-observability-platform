import os
import logging
import requests
import time
import socket
from typing import Dict, Any, Optional
from opentelemetry import trace, metrics as otel_metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

class ObservabilityClient:
    def __init__(self, service_name: str, otel_endpoint: str = None):
        self.service_name = service_name
        self.otel_endpoint = otel_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://scaibu.otel:4317")
        self.resource = Resource.create({"service.name": service_name})
        
        # Only init if host is resolvable
        self._is_ready = self._check_endpoint()
        if self._is_ready:
            self._init_tracing()
            self._init_metrics()
            self._init_logging()
        else:
            self.logger = logging.getLogger(self.service_name)
            self.logger.setLevel(logging.INFO)
            self.logger.warning(f"Observability endpoint {self.otel_endpoint} not resolvable. Tracing/Metrics disabled.")

    def _check_endpoint(self) -> bool:
        try:
            host = self.otel_endpoint.split("//")[-1].split(":")[0]
            socket.gethostbyname(host)
            return True
        except: return False

    def _init_tracing(self):
        tp = TracerProvider(resource=self.resource)
        tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=self.otel_endpoint, insecure=True)))
        trace.set_tracer_provider(tp)
        self.tracer = trace.get_tracer(self.service_name)

    def _init_metrics(self):
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=self.otel_endpoint, insecure=True))
        mp = MeterProvider(resource=self.resource, metric_readers=[reader])
        otel_metrics.set_meter_provider(mp)
        self.meter = otel_metrics.get_meter(self.service_name)

    def _init_logging(self):
        lp = LoggerProvider(resource=self.resource)
        lp.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=self.otel_endpoint, insecure=True)))
        set_logger_provider(lp)
        logging.getLogger().addHandler(LoggingHandler(level=logging.NOTSET, logger_provider=lp))
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.INFO)

    def log_info(self, msg, attrs=None): self.logger.info(msg, extra={"attributes": attrs or {}})
    def log_error(self, msg, attrs=None): self.logger.error(msg, extra={"attributes": attrs or {}})
    def increment_counter(self, name, val=1, attrs=None):
        if hasattr(self, 'meter'):
            self.meter.create_counter(name).add(val, attrs or {})

class ObservabilityVerifier:
    def __init__(self):
        self.prometheus_url = "http://scaibu.prometheus"
        self.loki_url = "http://scaibu.loki"
        self.jaeger_url = "http://scaibu.jaeger"

    def check_prometheus(self) -> bool:
        try:
            return requests.get(f"{self.prometheus_url}/-/healthy").status_code == 200
        except: return False

    def check_loki(self) -> bool:
        try:
            return requests.get(f"{self.loki_url}/ready").status_code == 200
        except: return False

    def check_jaeger(self) -> bool:
        try:
            return requests.get(f"{self.jaeger_url}/").status_code == 200
        except: return False
