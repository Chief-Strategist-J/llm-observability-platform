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
        
        logger.info("restarting_container: %s current_status=%s", container_name, container.status)
        
        try:
            container.restart(timeout=10)
            logger.info("container_restart_called: %s", container_name)
        except Exception as e:
            logger.warning("container_restart_failed trying stop/start: %s", str(e))
            try:
                container.stop(timeout=10)
                logger.info("container_stopped: %s", container_name)
            except Exception as e2:
                logger.warning("container_stop_failed: %s", str(e2))
            try:
                container.start()
                logger.info("container_started: %s", container_name)
            except Exception as e3:
                logger.error("container_start_failed: %s", str(e3))
                return {"success": False, "data": None, "error": "restart_failed"}
        
        start_time = time.time()
        ready = False
        
        for check_attempt in range(3):
            time.sleep(2)
            try:
                container.reload()
                status = container.status
                
                logger.info("container_status_check: %s status=%s attempt=%d elapsed=%.1fs", 
                          container_name, status, check_attempt + 1, time.time() - start_time)
                
                if status == "running":
                    try:
                        health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                    except Exception:
                        health = None
                    
                    logger.info("container_health_check: %s health=%s", container_name, health)
                    
                    if health in (None, "healthy", "starting"):
                        ready = True
                        break
            except Exception as e:
                logger.warning("container_reload_error: %s", str(e))
                status = "unknown"
        
        if not ready:
            logger.error("container_not_ready_after_checks")
        
        try:
            logs = container.logs(tail=100).decode("utf-8", errors="ignore")
            logger.info("container_logs_sample: %s\n%s", container_name, logs[-1500:])
            
            if "invalid keys" in logs.lower() or "cannot unmarshal" in logs.lower():
                logger.error("config_error_detected - OTel config is invalid")
                logger.error("config_error_logs: %s", logs[-800:])
                return {
                    "success": False, 
                    "data": {
                        "status": "config_invalid", 
                        "error": "otel_config_error", 
                        "logs": logs[-800:]
                    }, 
                    "error": "config_error"
                }
        except Exception as e:
            logger.warning("failed_to_fetch_logs: %s", str(e))
        
        logger.info("restart_source_logs waiting 8s for full startup")
        time.sleep(8)
        
        try:
            container.reload()
            final_status = container.status
            logger.info("restart_source_logs final_status=%s", final_status)
            
            if final_status != "running":
                return {
                    "success": False,
                    "data": {"status": final_status},
                    "error": "container_not_running"
                }
        except Exception as e:
            logger.error("final_status_check_failed: %s", str(e))
        
        return {"success": True, "data": {"status": "running", "elapsed": time.time() - start_time}, "error": None}
        
    except Exception as e:
        logger.error("restart_source_logs error: %s", str(e))
        return {"success": False, "data": None, "error": "unexpected_error"}