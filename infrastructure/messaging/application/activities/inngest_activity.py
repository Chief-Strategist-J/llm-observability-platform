import logging
from pathlib import Path

from temporalio import activity
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from infrastructure.orchestrator.base import YAMLContainerManager

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

INNGEST_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "inngest-dynamic-docker.yaml"


@activity.defn(name="start_inngest_activity")
async def start_inngest_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("start_inngest") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "inngest")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "start")
        
        logger.info("event=inngest_start_begin instance_id=%d yaml_path=%s", instance_id, INNGEST_YAML)
        
        try:
            manager = YAMLContainerManager(str(INNGEST_YAML), instance_id=instance_id)
            success = manager.start(restart_if_running=True)
            status = manager.get_status().value
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=inngest_start_complete instance_id=%d success=True status=%s", instance_id, status)
            else:
                span.set_status(Status(StatusCode.ERROR, "Start failed"))
                logger.error("event=inngest_start_failed instance_id=%d success=False status=%s", instance_id, status)
            
            return {"success": success, "service": "inngest", "instance_id": instance_id, "status": status}
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=inngest_start_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "inngest", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="stop_inngest_activity")
async def stop_inngest_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("stop_inngest") as span:
        instance_id = params.get("instance_id", 0)
        force = params.get("force", True)
        span.set_attribute("service", "inngest")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "stop")
        span.set_attribute("force", force)
        
        logger.info("event=inngest_stop_begin instance_id=%d force=%s", instance_id, force)
        
        try:
            manager = YAMLContainerManager(str(INNGEST_YAML), instance_id=instance_id)
            success = manager.stop(force=force)
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            
            logger.info("event=inngest_stop_complete instance_id=%d success=%s", instance_id, success)
            
            return {"success": success, "service": "inngest", "instance_id": instance_id, "force": force}
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=inngest_stop_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "inngest", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="restart_inngest_activity")
async def restart_inngest_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("restart_inngest") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "inngest")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "restart")
        
        logger.info("event=inngest_restart_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(str(INNGEST_YAML), instance_id=instance_id)
            success = manager.restart()
            status = manager.get_status().value
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            
            logger.info("event=inngest_restart_complete instance_id=%d success=%s status=%s", instance_id, success, status)
            
            return {"success": success, "service": "inngest", "instance_id": instance_id, "status": status}
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=inngest_restart_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "inngest", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="delete_inngest_activity")
async def delete_inngest_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("delete_inngest") as span:
        instance_id = params.get("instance_id", 0)
        remove_volumes = params.get("remove_volumes", True)
        remove_images = params.get("remove_images", True)
        remove_networks = params.get("remove_networks", False)
        
        span.set_attribute("service", "inngest")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "delete")
        span.set_attribute("remove_volumes", remove_volumes)
        span.set_attribute("remove_images", remove_images)
        span.set_attribute("remove_networks", remove_networks)
        
        logger.info("event=inngest_delete_begin instance_id=%d remove_volumes=%s remove_images=%s",
                   instance_id, remove_volumes, remove_images)
        
        try:
            manager = YAMLContainerManager(str(INNGEST_YAML), instance_id=instance_id)
            success = manager.delete(
                remove_volumes=remove_volumes,
                remove_images=remove_images,
                remove_networks=remove_networks
            )
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            
            logger.info("event=inngest_delete_complete instance_id=%d success=%s", instance_id, success)
            
            return {
                "success": success,
                "service": "inngest",
                "instance_id": instance_id,
                "volumes_removed": remove_volumes,
                "images_removed": remove_images,
                "networks_removed": remove_networks
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=inngest_delete_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "inngest", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="get_inngest_status_activity")
async def get_inngest_status_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("get_inngest_status") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "inngest")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "get_status")
        
        logger.info("event=inngest_status_check instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(str(INNGEST_YAML), instance_id=instance_id)
            status = manager.get_status()
            is_running = status.value == "running"
            
            span.set_attribute("result.status", status.value)
            span.set_attribute("result.is_running", is_running)
            span.set_status(Status(StatusCode.OK))
            
            logger.info("event=inngest_status_result instance_id=%d status=%s is_running=%s",
                       instance_id, status.value, is_running)
            
            return {
                "service": "inngest",
                "instance_id": instance_id,
                "status": status.value,
                "is_running": is_running
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=inngest_status_exception instance_id=%d error=%s", instance_id, str(e))
            return {"service": "inngest", "instance_id": instance_id, "status": "error", "is_running": False, "error": str(e)}

