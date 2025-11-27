"""
Observability Client for Python Microservices

This client provides a unified interface for logs, metrics, and tracing
using OpenTelemetry. All telemetry is sent to a central OTel Collector.

Usage:
    from infrastructure.observability.clients.python import ObservabilityClient
    
    obs = ObservabilityClient(service_name="my-service")
    
    # Logging
    obs.logger.info("User logged in", user_id=123)
    
    # Metrics
    obs.metrics.counter("requests_total", 1, {"endpoint": "/api/users"})
    
    # Tracing
    with obs.tracer.start_span("process_payment") as span:
        span.set_attribute("amount", 100.00)
        process_payment()
"""

import os
import logging
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
    """
    Unified observability client for Python microservices
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        environment: str = None,
        otel_endpoint: str = None,
        resource_attributes: Dict[str, Any] = None
    ):
        """
        Initialize observability client
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Environment (development, staging, production)
            otel_endpoint: OTel Collector endpoint (default: from env)
            resource_attributes: Additional resource attributes
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.otel_endpoint = otel_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", 
            "http://localhost:4317"
        )
        
        # Build resource attributes
        attrs = {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": self.environment,
        }
        if resource_attributes:
            attrs.update(resource_attributes)
        
        self.resource = Resource.create(attrs)
        
        # Initialize components
        self._init_tracing()
        self._init_metrics()
        self._init_logging()
    
    def _init_tracing(self):
        """Initialize tracing with OTel"""
        trace_provider = TracerProvider(resource=self.resource)
        otlp_span_exporter = OTLPSpanExporter(endpoint=self.otel_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_span_exporter)
        trace_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(trace_provider)
        
        self.tracer = trace.get_tracer(
            instrumenting_module_name=self.service_name,
            instrumenting_library_version=self.service_version
        )
    
    def _init_metrics(self):
        """Initialize metrics with OTel"""
        otlp_metric_exporter = OTLPMetricExporter(endpoint=self.otel_endpoint, insecure=True)
        metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)
        meter_provider = MeterProvider(resource=self.resource, metric_readers=[metric_reader])
        otel_metrics.set_meter_provider(meter_provider)
        
        self.meter = otel_metrics.get_meter(
            name=self.service_name,
            version=self.service_version
        )
        self.metrics = MetricsClient(self.meter)
    
    def _init_logging(self):
        """Initialize logging with OTel"""
        logger_provider = LoggerProvider(resource=self.resource)
        otlp_log_exporter = OTLPLogExporter(endpoint=self.otel_endpoint, insecure=True)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
        set_logger_provider(logger_provider)
        
        # Attach OTLP handler to Python logging
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)
        
        self.logger = StructuredLogger(self.service_name)
    
    def shutdown(self):
        """Gracefully shutdown and flush telemetry"""
        trace.get_tracer_provider().shutdown()
        otel_metrics.get_meter_provider().shutdown()


class StructuredLogger:
    """Structured logging wrapper"""
    
    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        self.logger.debug(message, extra=kwargs)


class MetricsClient:
    """Metrics wrapper for common metric types"""
    
    def __init__(self, meter):
        self.meter = meter
        self._counters = {}
        self._histograms = {}
        self._gauges = {}
    
    def counter(self, name: str, value: int = 1, attributes: Dict[str, Any] = None):
        """Increment a counter metric"""
        if name not in self._counters:
            self._counters[name] = self.meter.create_counter(
                name=name,
                description=f"Counter for {name}"
            )
        self._counters[name].add(value, attributes=attributes or {})
    
    def histogram(self, name: str, value: float, attributes: Dict[str, Any] = None):
        """Record a histogram value"""
        if name not in self._histograms:
            self._histograms[name] = self.meter.create_histogram(
                name=name,
                description=f"Histogram for {name}"
            )
        self._histograms[name].record(value, attributes=attributes or {})
    
    def gauge(self, name: str, value: float, attributes: Dict[str, Any] = None):
        """Set a gauge value"""
        if name not in self._gauges:
            self._gauges[name] = self.meter.create_observable_gauge(
                name=name,
                description=f"Gauge for {name}",
                callbacks=[lambda: [(value, attributes or {})]]
            )


# Singleton instance for easy access
_client_instance: Optional[ObservabilityClient] = None


def init_observability(
    service_name: str,
    service_version: str = "1.0.0",
    **kwargs
) -> ObservabilityClient:
    """
    Initialize the global observability client
    
    Usage:
        from infrastructure.observability.clients.python import init_observability
        
        obs = init_observability(service_name="my-service")
    """
    global _client_instance
    _client_instance = ObservabilityClient(
        service_name=service_name,
        service_version=service_version,
        **kwargs
    )
    return _client_instance


def get_client() -> ObservabilityClient:
    """Get the global observability client instance"""
    if _client_instance is None:
        raise RuntimeError("Observability client not initialized. Call init_observability() first.")
    return _client_instance
