import logging
import os
from typing import Optional
from infrastructure.observability.scripts.observability_client import ObservabilityClient

_client: Optional[ObservabilityClient] = None


def get_client() -> ObservabilityClient:
    global _client
    if _client is None:
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://172.28.0.10:4317")
        service_name = os.getenv("SERVICE_NAME", "llm-model-service")

        try:
            _client = ObservabilityClient(
                endpoint=otlp_endpoint, service_name=service_name
            )
        except Exception as e:
            logging.error(f"Failed to initialize ObservabilityClient: {e}")
            raise e

    return _client


def log_event(event_name: str, level: str = "info", **kwargs):
    """Log an event with structured attributes using OpenTelemetry."""
    try:
        client = get_client()

        attributes = {"event": event_name}
        attributes.update(kwargs)

        msg_parts = [f"event={event_name}"]
        for k, v in kwargs.items():
            msg_parts.append(f"{k}={v}")
        message = " ".join(msg_parts)

        if level.lower() in ("error", "critical"):
            client.log_error(message, attributes)
            client.increment_counter(
                "error_count", 1, {"event": event_name, "level": level}
            )
        else:
            client.log_info(message, attributes)

        current_span = trace.get_current_span()
        if current_span != trace.INVALID_SPAN:
            current_span.add_event(event_name, attributes)

    except Exception as e:
        logging.getLogger("llm_model_service").error(
            f"Failed to log event {event_name}: {e}"
        )


def get_tracer():
    try:
        return get_client().tracer
    except Exception:
        return trace.get_tracer("llm_model_service")


from opentelemetry import trace
from infrastructure.observability.scripts.observability_client import trace_with_details
