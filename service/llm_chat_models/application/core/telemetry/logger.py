import logging
import sys
import os
from typing import Dict, Any, Optional
from infrastructure.observability.scripts.observability_client import ObservabilityClient

# Initialize the observability client
# Using a singleton pattern to avoid multiple initializations
_client: Optional[ObservabilityClient] = None

def get_client() -> ObservabilityClient:
    global _client
    if _client is None:
        # Default OTLP endpoint from the observability_client.py but can be overridden
        # Using 172.28.0.10:4317 as per the file default
        otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://172.28.0.10:4317")
        service_name = os.getenv("SERVICE_NAME", "llm-model-service")
        
        try:
            _client = ObservabilityClient(endpoint=otlp_endpoint, service_name=service_name)
        except Exception as e:
            # Fallback to standard logging if OTLP fails (e.g. during local dev without stack)
            logging.error(f"Failed to initialize ObservabilityClient: {e}")
            # Create a dummy client or handle gracefully? 
            # For now, we'll let it fail or the client itself logs error.
            raise e
            
    return _client

def log_event(event_name: str, level: str = "info", **kwargs):
    """
    Log an event with structured attributes using OpenTelemetry.
    """
    try:
        client = get_client()
        
        # Prepare attributes
        attributes = {"event": event_name}
        attributes.update(kwargs)
        
        # Format message for human readability
        msg_parts = [f"event={event_name}"]
        for k, v in kwargs.items():
            msg_parts.append(f"{k}={v}")
        message = " ".join(msg_parts)
        
        # Log based on level
        if level.lower() == "error" or level.lower() == "critical":
            client.log_error(message, attributes)
            # Also increment error counter
            client.increment_counter("error_count", 1, {"event": event_name, "level": level})
        else:
            client.log_info(message, attributes)
            
        # Trace span for significant events (optional, can be expanded)
        # Using the current span if active, or logging as event
        current_span = trace.get_current_span()
        if current_span != trace.INVALID_SPAN:
            current_span.add_event(event_name, attributes)
            
    except Exception as e:
        # Fallback to standard logging if everything fails
        logging.getLogger("llm_model_service").error(f"Failed to log event {event_name}: {e}")

def get_tracer():
    try:
        return get_client().tracer
    except:
        return trace.get_tracer("llm_model_service")

# Re-export needed components
from opentelemetry import trace
from infrastructure.observability.scripts.observability_client import trace_with_details


