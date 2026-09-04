import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger("python_shared.telemetry")

def setup_telemetry(service_name: str, console_export: bool = False) -> trace.Tracer:
    """Initialize OpenTelemetry TracerProvider for service."""
    resource = Resource.create(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    if console_export:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        
    trace.set_tracer_provider(provider)
    logger.info(f"OpenTelemetry tracer initialized for service: {service_name}")
    return trace.get_tracer(service_name)

def get_tracer(service_name: str) -> trace.Tracer:
    return trace.get_tracer(service_name)
