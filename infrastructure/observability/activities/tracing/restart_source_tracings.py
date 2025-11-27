import logging
import time
from typing import Dict, Any
from temporalio import activity
import docker

logger = logging.getLogger(__name__)

@activity.defn
async def restart_source_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("restart_source_tracings started with params: %s", params)
    container_name = params.get("container_name")
    timeout_seconds = int(params.get("timeout_seconds", 60))
    if not container_name:
        logger.error("restart_source_tracings missing_container_name")
        return {"success": False, "data": None, "error": "missing_container_name"}
    try:
        client = docker.from_env()
        logger.info("restart_source_tracings docker client created successfully")
    except Exception as e:
        logger.error("restart_source_tracings docker_client_error: %s", str(e), exc_info=True)
        return {"success": False, "data": None, "error": "docker_client_error"}
    try:
        container = None
        try:
            container = client.containers.get(container_name)
            logger.info("restart_source_tracings found container by get: %s", container_name)
        except Exception:
            logger.info("restart_source_tracings container.get failed, searching in list")
            for c in client.containers.list(all=True):
                if c.name == container_name:
                    container = c
                    logger.info("restart_source_tracings found container in list: %s", container_name)
                    break
        if container is None:
            logger.error("restart_source_tracings container_not_found: %s", container_name)
            return {"success": False, "data": None, "error": "container_not_found"}
        
        logger.info("restart_source_tracings restarting container: %s current_status=%s", container_name, container.status)
        
        try:
            container.restart(timeout=10)
            logger.info("restart_source_tracings container_restart_called: %s", container_name)
        except Exception as e:
            logger.warning("restart_source_tracings container_restart_failed trying stop/start: %s", str(e))
            try:
                container.stop(timeout=10)
                logger.info("restart_source_tracings container_stopped: %s", container_name)
            except Exception as e2:
                logger.warning("restart_source_tracings container_stop_failed: %s", str(e2))
            try:
                container.start()
                logger.info("restart_source_tracings container_started: %s", container_name)
            except Exception as e3:
                logger.error("restart_source_tracings container_start_failed: %s", str(e3), exc_info=True)
                return {"success": False, "data": None, "error": "restart_failed"}
        
        start_time = time.time()
        ready = False
        
        for check_attempt in range(5):
            time.sleep(2)
            try:
                container.reload()
                status = container.status
                
                logger.info("restart_source_tracings container_status_check: %s status=%s attempt=%d elapsed=%.1fs", 
                          container_name, status, check_attempt + 1, time.time() - start_time)
                
                if status == "running":
                    try:
                        health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                    except Exception:
                        health = None
                    
                    logger.info("restart_source_tracings container_health_check: %s health=%s", container_name, health)
                    
                    if health in (None, "healthy", "starting"):
                        ready = True
                        logger.info("restart_source_tracings container ready: %s", container_name)
                        break
                else:
                    logger.warning("restart_source_tracings container not running: status=%s", status)
            except Exception as e:
                logger.warning("restart_source_tracings container_reload_error: %s", str(e))
                status = "unknown"
        
        if not ready:
            logger.error("restart_source_tracings container_not_ready_after_checks")
        
        try:
            logs = container.logs(tail=200).decode("utf-8", errors="ignore")
            logger.info("restart_source_tracings container_logs_sample: %s\n%s", container_name, logs[-2000:])
            
            if "invalid keys" in logs.lower() or "cannot unmarshal" in logs.lower():
                logger.error("restart_source_tracings config_error_detected - OTel config is invalid")
                logger.error("restart_source_tracings config_error_logs: %s", logs[-1000:])
                return {
                    "success": False, 
                    "data": {
                        "status": "config_invalid", 
                        "error": "otel_config_error", 
                        "logs": logs[-1000:]
                    }, 
                    "error": "config_error"
                }
            
            if "bind: address already in use" in logs.lower():
                logger.error("restart_source_tracings port_conflict detected in logs")
                logger.error("restart_source_tracings port_error_logs: %s", logs[-1000:])
            
            if "failed to create" in logs.lower() or "error" in logs.lower():
                logger.warning("restart_source_tracings potential issues detected in logs")
                
        except Exception as e:
            logger.warning("restart_source_tracings failed_to_fetch_logs: %s", str(e))
        
        logger.info("restart_source_tracings waiting 10s for full startup and OTLP receiver initialization")
        time.sleep(10)
        
        try:
            container.reload()
            final_status = container.status
            logger.info("restart_source_tracings final_status=%s", final_status)
            
            if final_status != "running":
                logger.error("restart_source_tracings container not running after restart")
                return {
                    "success": False,
                    "data": {"status": final_status},
                    "error": "container_not_running"
                }
        except Exception as e:
            logger.error("restart_source_tracings final_status_check_failed: %s", str(e), exc_info=True)
        
        elapsed = time.time() - start_time
        logger.info("restart_source_tracings completed: status=running elapsed=%.2fs", elapsed)
        return {"success": True, "data": {"status": "running", "elapsed": elapsed}, "error": None}
        
    except Exception as e:
        logger.error("restart_source_tracings error: %s", str(e), exc_info=True)
        return {"success": False, "data": None, "error": "unexpected_error"}
