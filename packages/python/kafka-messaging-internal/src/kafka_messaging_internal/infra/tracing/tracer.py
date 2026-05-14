"""OpenTelemetry tracer initialization - FIRST thing to run."""

import os
from opentelemetry import trace, resources
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


class TracerInitializer:
    """Initializes OTEL tracer with required attributes."""
    
    def __init__(self):
        self.service_name = os.getenv('OTEL_SERVICE_NAME', 'kafka-messaging-internal')
        self.service_version = os.getenv('OTEL_SERVICE_VERSION', '1.0.0')
        self.deployment_env = os.getenv('DEPLOYMENT_ENV', 'development')
        self.host_name = os.getenv('HOST_NAME', 'localhost')
        self.otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
        
    def initialize(self):
        """Initialize OTEL tracer - MUST be called before any other code."""
        # Create resource with ALL required attributes per migration.md
        resource = Resource.create({
            "service.name": self.service_name,
            "language.package-name": "kafka-messaging-internal",
            "service.version": self.service_version,
            "feature.name": "messaging",  # Will be overridden per feature
            "api.version": "v1",
            "deployment.env": self.deployment_env,
            "host.name": self.host_name,
        })
        
        # Initialize exporter
        exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
        
        # Initialize tracer provider
        tracer_provider = TracerProvider(
            resource=resource,
            span_processors=[BatchSpanProcessor(exporter)]
        )
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument libraries
        FastAPIInstrumentor().instrument(tracer_provider=tracer_provider)
        Psycopg2Instrumentor().instrument(tracer_provider=tracer_provider)
        RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
        
        return trace.get_tracer(__name__)
    
    def get_tracer(self, name: str):
        """Get tracer with required attributes."""
        tracer = trace.get_tracer(name)
        return tracer


# Global tracer initializer
_tracer_initializer: TracerInitializer = None


def initialize_tracer() -> trace.Tracer:
    """Initialize global tracer - call this FIRST in application startup."""
    global _tracer_initializer
    if _tracer_initializer is None:
        _tracer_initializer = TracerInitializer()
        return _tracer_initializer.initialize()
    return trace.get_tracer(__name__)


def get_tracer(name: str) -> trace.Tracer:
    """Get tracer instance."""
    return trace.get_tracer(name)


def create_root_span(operation_name: str, attributes: dict = None) -> trace.Span:
    """Create root span with required attributes."""
    tracer = get_tracer(__name__)
    
    # Get required attributes from environment
    service_name = os.getenv('OTEL_SERVICE_NAME', 'kafka-messaging-internal')
    service_version = os.getenv('OTEL_SERVICE_VERSION', '1.0.0')
    deployment_env = os.getenv('DEPLOYMENT_ENV', 'development')
    host_name = os.getenv('HOST_NAME', 'localhost')
    
    # Create span with required attributes
    span = tracer.start_span(operation_name)
    
    # Set required attributes
    span.set_attribute("service.name", service_name)
    span.set_attribute("service.version", service_version)
    span.set_attribute("deployment.env", deployment_env)
    span.set_attribute("host.name", host_name)
    span.set_attribute("feature.name", attributes.get("feature.name", "unknown"))
    span.set_attribute("api.version", attributes.get("api.version", "v1"))
    
    # Set additional attributes
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
    
    return span


def finish_span(span: trace.Span, error: Exception = None):
    """Finish span with error handling."""
    if error:
        span.record_error(error)
        span.set_status(trace.Status.ERROR)
    else:
        span.set_status(trace.Status.OK)
    
    span.end()
