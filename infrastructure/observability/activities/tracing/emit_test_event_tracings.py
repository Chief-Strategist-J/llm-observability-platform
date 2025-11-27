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
    logger.info(
        "emit_test_event_tracings_start params_keys=%s",
        list(params.keys())
    )

    otlp_endpoint = params.get("otlp_endpoint", "http://localhost:4317")
    service_name = params.get("service_name", "test-tracing-service")
    span_name = params.get("span_name", "test-span")
    wait_ms = int(params.get("latency_wait_ms", 500))

    logger.debug(
        "emit_test_event_tracings_params otlp_endpoint=%s service_name=%s span_name=%s wait_ms=%d",
        otlp_endpoint,
        service_name,
        span_name,
        wait_ms,
    )

    try:
        token = f"SYNTH-TRACE-{uuid.uuid4().hex}"
        logger.debug("generated_trace_token token=%s", token)

        resource = Resource.create({"service.name": service_name, "test.token": token})
        logger.debug("resource_created service_name=%s token=%s", service_name, token)

        provider = TracerProvider(resource=resource)
        logger.debug("tracer_provider_initialized")

        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        logger.debug(
            "span_exporter_configured endpoint=%s insecure=%s",
            otlp_endpoint, True
        )

        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)
        logger.debug("global_tracer_set tracer_name=%s", __name__)

        with tracer.start_as_current_span(span_name) as span:
            logger.debug("span_started span_name=%s", span_name)

            span.set_attribute("test.token", token)
            span.set_attribute("test.timestamp", int(time.time()))
            span.set_attribute("test.type", "synthetic")

            logger.debug(
                "span_attributes_set token=%s timestamp=%d",
                token, int(time.time())
            )

            span.add_event("test_event", {"message": "This is a test trace event"})
            logger.debug("span_event_added event_name=test_event")

            await asyncio.sleep(0.1)

        provider.force_flush()
        logger.debug("force_flush_completed")

        await asyncio.sleep(wait_ms / 1000.0)
        await asyncio.sleep(2.0)

        logger.info(
            "emit_test_event_tracings_complete token=%s endpoint=%s service_name=%s span_name=%s",
            token, otlp_endpoint, service_name, span_name
        )

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
        logger.exception(
            "emit_test_event_tracings_error error=emit_failed exception=%s",
            e
        )
        return {"success": False, "data": None, "error": "emit_failed"}
