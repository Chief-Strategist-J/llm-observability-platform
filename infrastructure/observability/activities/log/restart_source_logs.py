# infrastructure/observability/activities/log/restart_source_logs.py
import logging
import time
from typing import Dict, Any
from temporalio import activity
import docker

logger = logging.getLogger(__name__)

@activity.defn
async def restart_source_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("restart_source_logs started with params: %s", params)
    container_name = params.get("container_name")
    timeout_seconds = int(params.get("timeout_seconds", 60))
    if not container_name:
        logger.error("missing_container_name")
        return {"success": False, "data": None, "error": "missing_container_name"}
    try:
        client = docker.from_env()
    except Exception as e:
        logger.error("docker_client_error: %s", str(e))
        return {"success": False, "data": None, "error": "docker_client_error"}
    try:
        container = None
        try:
            container = client.containers.get(container_name)
        except Exception:
            for c in client.containers.list(all=True):
                if c.name == container_name:
                    container = c
                    break
        if container is None:
            logger.error("container_not_found: %s", container_name)
            return {"success": False, "data": None, "error": "container_not_found"}
        logger.info("restarting_container: %s", container_name)
        try:
            container.restart(timeout=10)
        except Exception:
            try:
                container.stop(timeout=10)
            except Exception:
                pass
            try:
                container.start()
            except Exception as e:
                logger.error("container_restart_failed: %s", str(e))
                return {"success": False, "data": None, "error": "restart_failed"}
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                container.reload()
                status = container.status
            except Exception:
                status = None
            if status == "running":
                try:
                    health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                except Exception:
                    health = None
                if health in (None, "healthy", "starting"):
                    logger.info("container_status_ok: %s", status)
                    return {"success": True, "data": {"status": status, "health": health}, "error": None}
            time.sleep(1)
        try:
            container.reload()
            final_status = container.status
        except Exception:
            final_status = "unknown"
        logger.error("restart_timeout: status=%s", final_status)
        return {"success": False, "data": {"status": final_status}, "error": "timeout"}
    except Exception as e:
        logger.error("restart_source_logs error: %s", str(e))
        return {"success": False, "data": None, "error": "unexpected_error"}
