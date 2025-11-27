import logging
import time
import uuid
import asyncio
from typing import Dict, Any
from temporalio import activity
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

@activity.defn
async def emit_test_event_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("emit_test_event_tracings started with params: %s", params)

    otlp_endpoint = params.get("otlp_endpoint", "http://localhost:4317")
    service_name = params.get("service_name", "test-tracing-service")
    span_name = params.get("span_name", "test-span")
    wait_ms = int(params.get("latency_wait_ms", 500))

    try:
        # Create a unique trace token for verification
        token = f"SYNTH-TRACE-{uuid.uuid4().hex}"
        
        # Set up OpenTelemetry
        resource = Resource.create({"service.name": service_name, "test.token": token})
        provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)

        # Create test span
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("test.token", token)
            span.set_attribute("test.timestamp", int(time.time()))
            span.set_attribute("test.type", "synthetic")
            span.add_event("test_event", {"message": "This is a test trace event"})
            
            # Simulate some work
            await asyncio.sleep(0.1)

        # Force flush to ensure spans are sent
        provider.force_flush()
        
        # Wait for ingestion latency
        await asyncio.sleep(wait_ms / 1000.0)
        await asyncio.sleep(2.0)

        logger.info("emit_test_event_tracings completed token=%s endpoint=%s", token, otlp_endpoint)
        return {
            "success": True, 
            "data": {
                "token": token, 
                "endpoint": otlp_endpoint,
                "service_name": service_name,
                "span_name": span_name
            }, 
            "error": None
        }

    except Exception as e:
        logger.exception("emit_test_event_tracings error: %s", e)
        return {"success": False, "data": None, "error": "emit_failed"}
