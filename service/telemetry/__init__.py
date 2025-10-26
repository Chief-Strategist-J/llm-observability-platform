"""OpenTelemetry Telemetry Initialization Module.

This module provides centralized telemetry setup for the LLM chatbot application.
It handles graceful degradation when observability services are not available.

Features:
- Automatic service detection and fallback
- Graceful degradation when services are unavailable
- Configurable sampling and batching
- Resource attribute enrichment
- Support for traces, metrics, and logs

"""

import logging
import os
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as OTLPMetricHTTPExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPSpanHTTPExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.semconv.resource import ResourceAttributes

__all__ = [
    "TelemetryManager",
    "get_telemetry_manager",
    "initialize_telemetry",
    "get_tracer",
    "get_meter",
    "shutdown_telemetry",
]

# Configure logging for telemetry module
telemetry_logger = logging.getLogger("telemetry")
telemetry_logger.setLevel(logging.INFO)

# Create console handler for telemetry logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
telemetry_logger.addHandler(console_handler)


class TelemetryManager:
    """
    Manages OpenTelemetry setup with graceful degradation.
    """

    def __init__(
        self,
        service_name: str = "llm-chatbot",
        service_version: str = "1.0.0",
        environment: str = "development",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        enable_logging: bool = True,
        otlp_endpoint: str | None = None,
        otlp_insecure: bool = True,
        sampling_ratio: float = 1.0,  # 1.0 = 100% sampling, 0.1 = 10% sampling
    ):
        """Initialize telemetry manager.

        Args:
            service_name: Name of the service for telemetry
            service_version: Version of the service
            environment: Environment (development, staging, production)
            enable_tracing: Whether to enable distributed tracing
            enable_metrics: Whether to enable metrics collection
            enable_logging: Whether to enable structured logging
            otlp_endpoint: Custom OTLP endpoint (auto-detected if None)
            otlp_insecure: Whether to use insecure OTLP connection
            sampling_ratio: Trace sampling ratio (0.0 to 1.0)

        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics
        self.enable_logging = enable_logging
        self.sampling_ratio = sampling_ratio

        # Auto-detect OTLP endpoint if not provided
        if otlp_endpoint is None:
            otlp_endpoint = self._detect_otlp_endpoint()

        self.otlp_endpoint = otlp_endpoint
        self.otlp_insecure = otlp_insecure

        # Initialize components
        self._tracer_provider: TracerProvider | None = None
        self._meter_provider: MeterProvider | None = None
        self._tracer = None
        self._meter = None

        telemetry_logger.info(
            f"Initializing TelemetryManager for {service_name} v{service_version} "
            f"in {environment} environment"
        )

    def _detect_otlp_endpoint(self) -> str:
        """
        Detect OTLP endpoint from environment or use default.
        """
        # Try environment variable first
        env_endpoint = os.getenv("OTLP_ENDPOINT")
        if env_endpoint:
            return env_endpoint

        # Check if running in Docker with observability network
        try:
            import socket

            # Try to connect to OpenTelemetry Collector
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("otel-collector", 4317))
            sock.close()

            if result == 0:
                return "http://otel-collector:4318"  # HTTP endpoint
            telemetry_logger.warning(
                "OpenTelemetry Collector not available at otel-collector:4317, "
                "using localhost fallback"
            )
        except Exception as e:
            telemetry_logger.debug(f"Error detecting OTLP endpoint: {e}")

        # Fallback to localhost (for development)
        return "http://localhost:4318"

    def _is_service_available(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """
        Check if a service is available.
        """
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _setup_resource_attributes(self) -> Resource:
        """
        Set up resource attributes for telemetry.
        """
        return Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: self.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
                "service.namespace": "llm-chatbot",
            }
        )

    def _setup_tracing(self) -> None:
        """
        Set up distributed tracing.
        """
        if not self.enable_tracing:
            telemetry_logger.info("Tracing disabled")
            return

        try:
            # Create resource
            resource = self._setup_resource_attributes()

            # Set up tracer provider with default sampling
            self._tracer_provider = TracerProvider(resource=resource)

            # Set up exporters
            exporters = []

            # Try OTLP exporter first
            try:
                otlp_exporter = OTLPSpanHTTPExporter(
                    endpoint=f"{self.otlp_endpoint}/v1/traces",
                )
                exporters.append(otlp_exporter)
                telemetry_logger.info("OTLP trace exporter configured")
            except Exception as e:
                telemetry_logger.warning(f"OTLP trace exporter failed: {e}")
                telemetry_logger.info("Falling back to console exporter")

            # Always add console exporter as fallback
            try:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                console_exporter = ConsoleSpanExporter()
                exporters.append(console_exporter)
            except ImportError:
                telemetry_logger.warning(
                    "ConsoleSpanExporter not available, tracing limited"
                )

            # Set up span processors
            for exporter in exporters:
                span_processor = BatchSpanProcessor(exporter)
                self._tracer_provider.add_span_processor(span_processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self._tracer_provider)

            # Get tracer instance
            self._tracer = trace.get_tracer(__name__)

            telemetry_logger.info(
                f"Tracing initialized with {len(exporters)} exporters "
                f"(sampling ratio: {self.sampling_ratio})"
            )

        except Exception as e:
            telemetry_logger.error(f"Failed to initialize tracing: {e}")
            self.enable_tracing = False

    def _setup_metrics(self) -> None:
        """
        Set up metrics collection.
        """
        if not self.enable_metrics:
            telemetry_logger.info("Metrics disabled")
            return

        try:
            # Create resource
            resource = self._setup_resource_attributes()

            # Set up metric readers and exporters
            metric_readers = []

            # Try OTLP metric exporter
            try:
                otlp_metric_exporter = OTLPMetricHTTPExporter(
                    endpoint=f"{self.otlp_endpoint}/v1/metrics",
                    insecure=True,
                )

                metric_reader = PeriodicExportingMetricReader(
                    exporter=otlp_metric_exporter,
                    export_interval_millis=5000,  # 5 seconds
                )
                metric_readers.append(metric_reader)
                telemetry_logger.info("OTLP metrics exporter configured")
            except Exception as e:
                telemetry_logger.warning(f"OTLP metrics exporter failed: {e}")
                telemetry_logger.info("Using console metrics only")

            # Always add console metric reader as fallback
            from opentelemetry.sdk.metrics.export import (
                MetricExporter,
                MetricExportResult,
            )

            class ConsoleMetricExporter(MetricExporter):
                def __init__(self):
                    super().__init__()

                def export(self, metrics_data, timeout_millis=5000):
                    telemetry_logger.info(f"Console Metrics: {metrics_data}")
                    return MetricExportResult.SUCCESS

                def force_flush(self, timeout_millis=10000):
                    return True

                def shutdown(self, timeout_millis=30000, **kwargs):
                    pass

            console_metric_reader = PeriodicExportingMetricReader(
                exporter=ConsoleMetricExporter(),
                export_interval_millis=10000,  # 10 seconds
            )
            metric_readers.append(console_metric_reader)

            # Set up meter provider
            self._meter_provider = MeterProvider(
                resource=resource,
                metric_readers=metric_readers,
            )

            # Set as global meter provider
            metrics.set_meter_provider(self._meter_provider)

            # Get meter instance
            self._meter = metrics.get_meter(__name__)

            telemetry_logger.info(
                f"Metrics initialized with {len(metric_readers)} readers"
            )

        except Exception as e:
            telemetry_logger.error(f"Failed to initialize metrics: {e}")
            self.enable_metrics = False

    def _setup_logging(self) -> None:
        """
        Set up structured logging.
        """
        if not self.enable_logging:
            telemetry_logger.info("Logging disabled")
            return

        try:
            # Import logging instrumentation
            from opentelemetry.instrumentation.logging import LoggingInstrumentor

            # Instrument standard logging
            LoggingInstrumentor().instrument(
                set_logging_format=True,
                logging_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

            telemetry_logger.info("Structured logging initialized")

        except Exception as e:
            telemetry_logger.error(f"Failed to initialize logging: {e}")
            self.enable_logging = False

    def initialize(self) -> bool:
        """
        Initialize all telemetry components.
        """
        telemetry_logger.info("Starting telemetry initialization...")

        # Set up components in order
        self._setup_tracing()
        self._setup_metrics()
        self._setup_logging()

        # Summary
        initialized_components = []
        if self.enable_tracing and self._tracer:
            initialized_components.append("tracing")
        if self.enable_metrics and self._meter:
            initialized_components.append("metrics")
        if self.enable_logging:
            initialized_components.append("logging")

        if initialized_components:
            telemetry_logger.info(
                f"Telemetry initialization completed: {', '.join(initialized_components)}"
            )
            return True
        telemetry_logger.warning(
            "No telemetry components were successfully initialized"
        )
        return False

    def get_tracer(self, name: str = __name__) -> trace.Tracer | None:
        """
        Get a tracer instance.
        """
        if self.enable_tracing and self._tracer:
            return self._tracer
        return None

    def get_meter(self, name: str = __name__) -> metrics.Meter | None:
        """
        Get a meter instance.
        """
        if self.enable_metrics and self._meter:
            return self._meter
        return None

    def shutdown(self) -> None:
        """
        Shutdown telemetry and flush remaining data.
        """
        telemetry_logger.info("Shutting down telemetry...")

        try:
            if self._tracer_provider:
                self._tracer_provider.shutdown()

            if self._meter_provider:
                self._meter_provider.shutdown()

            telemetry_logger.info("Telemetry shutdown completed")
        except Exception as e:
            telemetry_logger.error(f"Error during telemetry shutdown: {e}")


# Global telemetry manager instance
_telemetry_manager: TelemetryManager | None = None


def get_telemetry_manager() -> TelemetryManager:
    """
    Get the global telemetry manager instance.
    """
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager


def initialize_telemetry(
    service_name: str = "llm-chatbot",
    service_version: str = "1.0.0",
    environment: str | None = None,
    **kwargs,
) -> bool:
    """
    Initialize telemetry with automatic configuration.
    """
    # Auto-detect environment if not provided
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    # Create and initialize telemetry manager
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        **kwargs,
    )

    return _telemetry_manager.initialize()


def get_tracer(name: str = __name__) -> trace.Tracer | None:
    """
    Get a tracer instance (convenience function)
    """
    manager = get_telemetry_manager()
    return manager.get_tracer(name)


def get_meter(name: str = __name__) -> metrics.Meter | None:
    """
    Get a meter instance (convenience function)
    """
    manager = get_telemetry_manager()
    return manager.get_meter(name)


def shutdown_telemetry() -> None:
    """
    Shutdown telemetry (convenience function)
    """
    global _telemetry_manager
    if _telemetry_manager:
        _telemetry_manager.shutdown()
        _telemetry_manager = None
