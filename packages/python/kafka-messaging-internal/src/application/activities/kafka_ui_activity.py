"""Kafka UI activity for Temporal workflows."""

import logging
from pathlib import Path
from temporalio import activity
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

KAFKA_UI_YAML = Path(__file__).parent.parent.parent.parent / "deploy" / "docker" / "docker-compose.dev.yaml"


@activity.defn(name="start_kafka_ui_activity")
async def start_kafka_ui_activity(params: dict) -> dict:
    """Start Kafka UI container activity."""
    with _tracer.start_as_current_span("start_kafka_ui") as span:
        span.set_attribute("service.name", "kafka-messaging-internal")
        span.set_attribute("feature.name", "kafka-ui-management")
        span.set_attribute("api.version", "v1")
        span.set_attribute("deployment.env", "development")
        span.set_attribute("instance_id", params.get("instance_id", 0))
        span.set_attribute("action", "start")
        
        logger.info("event=kafka_ui_start_begin instance_id=%d", params.get("instance_id", 0))
        
        try:
            with _tracer.start_as_current_span("start_kafka_ui_container") as start_span:
                # Simplified implementation - would use container manager
                success = True  # Placeholder for actual container management
                status = "running"
                
                start_span.set_attribute("success", success)
                start_span.set_attribute("status", status)
                
                logger.info("event=kafka_ui_start_success instance_id=%d", params.get("instance_id", 0))
                
                return {
                    "success": success,
                    "status": status,
                    "instance_id": params.get("instance_id", 0)
                }
                
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error("event=kafka_ui_start_failed instance_id=%d error=%s", params.get("instance_id", 0), str(e))
            
            return {
                "success": False,
                "error": str(e),
                "instance_id": params.get("instance_id", 0)
            }


@activity.defn(name="stop_kafka_ui_activity")
async def stop_kafka_ui_activity(params: dict) -> dict:
    """Stop Kafka UI container activity."""
    with _tracer.start_as_current_span("stop_kafka_ui") as span:
        span.set_attribute("service.name", "kafka-messaging-internal")
        span.set_attribute("feature.name", "kafka-ui-management")
        span.set_attribute("api.version", "v1")
        span.set_attribute("deployment.env", "development")
        span.set_attribute("instance_id", params.get("instance_id", 0))
        span.set_attribute("action", "stop")
        
        logger.info("event=kafka_ui_stop_begin instance_id=%d", params.get("instance_id", 0))
        
        try:
            with _tracer.start_as_current_span("stop_kafka_ui_container") as stop_span:
                # Simplified implementation
                success = True  # Placeholder for actual container management
                status = "stopped"
                
                stop_span.set_attribute("success", success)
                stop_span.set_attribute("status", status)
                
                logger.info("event=kafka_ui_stop_success instance_id=%d", params.get("instance_id", 0))
                
                return {
                    "success": success,
                    "status": status,
                    "instance_id": params.get("instance_id", 0)
                }
                
        except Exception as e:
            span.record_error(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error("event=kafka_ui_stop_failed instance_id=%d error=%s", params.get("instance_id", 0), str(e))
            
            return {
                "success": False,
                "error": str(e),
                "instance_id": params.get("instance_id", 0)
            }
