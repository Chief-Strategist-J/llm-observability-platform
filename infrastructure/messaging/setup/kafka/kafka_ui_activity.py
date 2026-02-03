from pathlib import Path
import logging
from temporalio import activity
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from infrastructure.orchestrator.base import YAMLContainerManager

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

KAFKA_UI_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "kafka-ui-dynamic-docker.yaml"


def _build_env(instance_id: int, params: dict) -> dict:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("KAFKA_UI_INSTANCE_ID", str(instance_id))
    
    # Force port 8082 to avoid conflict with Temporal UI
    env_overrides.setdefault("SERVER_PORT", "8082")
    env_overrides.setdefault("KAFKA_UI_PORT", "8082")
    
    # Connect to Kafka on port 9094
    kafka_instance_id = params.get("kafka_instance_id", instance_id)
    env_overrides.setdefault("KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS", f"kafka-instance-{kafka_instance_id}:9094")
    
    return env_overrides


@activity.defn(name="start_kafka_ui_activity")
async def start_kafka_ui_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("start_kafka_ui") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka-ui")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "start")
        
        logger.info("event=kafka_ui_start_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_UI_YAML), 
                instance_id=instance_id,
                env_vars=_build_env(instance_id, params)
            )
            
            success = manager.start(restart_if_running=True)
            status = manager.get_status().value
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_ui_start_complete instance_id=%d success=True status=%s", instance_id, status)
            else:
                span.set_status(Status(StatusCode.ERROR, "Start failed"))
                logger.error("event=kafka_ui_start_failed instance_id=%d status=%s", instance_id, status)
            
            return {
                "success": success,
                "service": "kafka-ui",
                "instance_id": instance_id,
                "status": status
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_ui_start_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka-ui", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="stop_kafka_ui_activity")
async def stop_kafka_ui_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("stop_kafka_ui") as span:
        instance_id = params.get("instance_id", 0)
        force = params.get("force", True)
        span.set_attribute("service", "kafka-ui")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "stop")
        span.set_attribute("force", force)
        
        logger.info("event=kafka_ui_stop_begin instance_id=%d force=%s", instance_id, force)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_UI_YAML), 
                instance_id=instance_id,
                env_vars=_build_env(instance_id, params)
            )
            
            success = manager.stop(force=force)
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_ui_stop_complete instance_id=%d success=True", instance_id)
            
            return {
                "success": success,
                "service": "kafka-ui",
                "instance_id": instance_id,
                "force": force
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_ui_stop_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka-ui", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="restart_kafka_ui_activity")
async def restart_kafka_ui_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("restart_kafka_ui") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka-ui")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "restart")
        
        logger.info("event=kafka_ui_restart_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_UI_YAML), 
                instance_id=instance_id,
                env_vars=_build_env(instance_id, params)
            )
            
            success = manager.restart()
            status = manager.get_status().value
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_ui_restart_complete instance_id=%d success=True status=%s", instance_id, status)
            
            return {
                "success": success,
                "service": "kafka-ui",
                "instance_id": instance_id,
                "status": status
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_ui_restart_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka-ui", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="delete_kafka_ui_activity")
async def delete_kafka_ui_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("delete_kafka_ui") as span:
        instance_id = params.get("instance_id", 0)
        remove_volumes = params.get("remove_volumes", True)
        remove_images = params.get("remove_images", True)
        remove_networks = params.get("remove_networks", False)
        
        span.set_attribute("service", "kafka-ui")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "delete")
        
        logger.info("event=kafka_ui_delete_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_UI_YAML), 
                instance_id=instance_id,
                env_vars=_build_env(instance_id, params)
            )
            
            success = manager.delete(
                remove_volumes=remove_volumes,
                remove_images=remove_images,
                remove_networks=remove_networks
            )
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_ui_delete_complete instance_id=%d success=True", instance_id)
            
            return {
                "success": success,
                "service": "kafka-ui",
                "instance_id": instance_id,
                "volumes_removed": remove_volumes,
                "images_removed": remove_images,
                "networks_removed": remove_networks
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_ui_delete_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka-ui", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="get_kafka_ui_status_activity")
async def get_kafka_ui_status_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("get_kafka_ui_status") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka-ui")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "get_status")
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_UI_YAML), 
                instance_id=instance_id,
                env_vars=_build_env(instance_id, params)
            )
            
            status = manager.get_status()
            is_running = status.value == "running"
            
            span.set_attribute("result.status", status.value)
            span.set_attribute("result.is_running", is_running)
            span.set_status(Status(StatusCode.OK))
            
            return {
                "service": "kafka-ui",
                "instance_id": instance_id,
                "status": status.value,
                "is_running": is_running
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_ui_status_exception instance_id=%d error=%s", instance_id, str(e))
            return {"service": "kafka-ui", "instance_id": instance_id, "status": "error", "is_running": False, "error": str(e)}
