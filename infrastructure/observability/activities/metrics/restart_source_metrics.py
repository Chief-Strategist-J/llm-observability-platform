import logging
import time
from typing import Dict, Any
from temporalio import activity
import docker

logger = logging.getLogger(__name__)

@activity.defn
async def restart_source_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("restart_source_metrics_start params=%s", list(params.keys()))
    container_name = params.get("container_name")
    timeout_seconds = int(params.get("timeout_seconds", 60))
    
    logger.debug("restart_source_metrics_params container=%s timeout=%s", container_name, timeout_seconds)
    
    if not container_name:
        logger.error("restart_source_metrics_missing_container_name")
        return {"success": False, "data": None, "error": "missing_container_name"}
    
    try:
        client = docker.from_env()
        logger.info("restart_source_metrics_docker_client_created")
    except Exception as e:
        logger.error("restart_source_metrics_docker_client_error error=%s", str(e))
        return {"success": False, "data": None, "error": "docker_client_error"}
    
    try:
        container = None
        try:
            container = client.containers.get(container_name)
            logger.info("restart_source_metrics_container_found name=%s", container_name)
        except Exception:
            logger.info("restart_source_metrics_container_search name=%s", container_name)
            for c in client.containers.list(all=True):
                if c.name == container_name:
                    container = c
                    logger.info("restart_source_metrics_container_found_in_list name=%s", container_name)
                    break
        
        if container is None:
            logger.error("restart_source_metrics_container_not_found name=%s", container_name)
            return {"success": False, "data": None, "error": "container_not_found"}
        
        logger.info("restart_source_metrics_restarting name=%s status=%s", container_name, container.status)
        
        try:
            container.restart(timeout=10)
            logger.info("restart_source_metrics_restart_called name=%s", container_name)
        except Exception as e:
            logger.warning("restart_source_metrics_restart_failed_trying_stop_start name=%s error=%s", 
                         container_name, str(e))
            try:
                container.stop(timeout=10)
                logger.info("restart_source_metrics_stopped name=%s", container_name)
            except Exception as e2:
                logger.warning("restart_source_metrics_stop_failed name=%s error=%s", container_name, str(e2))
            try:
                container.start()
                logger.info("restart_source_metrics_started name=%s", container_name)
            except Exception as e3:
                logger.error("restart_source_metrics_start_failed name=%s error=%s", container_name, str(e3))
                return {"success": False, "data": None, "error": "restart_failed"}
        
        start_time = time.time()
        ready = False
        
        for check_attempt in range(5):
            time.sleep(2)
            try:
                container.reload()
                status = container.status
                
                logger.info("restart_source_metrics_status_check name=%s status=%s attempt=%s elapsed=%.1f", 
                          container_name, status, check_attempt + 1, time.time() - start_time)
                
                if status == "running":
                    try:
                        health = container.attrs.get("State", {}).get("Health", {}).get("Status")
                    except Exception:
                        health = None
                    
                    logger.info("restart_source_metrics_health_check name=%s health=%s", container_name, health)
                    
                    if health in (None, "healthy", "starting"):
                        ready = True
                        logger.info("restart_source_metrics_ready name=%s", container_name)
                        break
                else:
                    logger.warning("restart_source_metrics_not_running name=%s status=%s", container_name, status)
            except Exception as e:
                logger.warning("restart_source_metrics_reload_error name=%s error=%s", container_name, str(e))
                status = "unknown"
        
        if not ready:
            logger.error("restart_source_metrics_not_ready_after_checks name=%s", container_name)
        
        try:
            logs = container.logs(tail=200).decode("utf-8", errors="ignore")
            logger.info("restart_source_metrics_logs name=%s\n%s", container_name, logs[-2000:])
        except Exception as e:
            logger.warning("restart_source_metrics_logs_fetch_failed name=%s error=%s", container_name, str(e))
        
        logger.info("restart_source_metrics_waiting name=%s", container_name)
        time.sleep(10)
        
        try:
            container.reload()
            final_status = container.status
            logger.info("restart_source_metrics_final_status name=%s status=%s", container_name, final_status)
            
            if final_status != "running":
                logger.error("restart_source_metrics_not_running_final name=%s status=%s", 
                           container_name, final_status)
                return {
                    "success": False,
                    "data": {"status": final_status},
                    "error": "container_not_running"
                }
        except Exception as e:
            logger.error("restart_source_metrics_final_check_failed name=%s error=%s", 
                        container_name, str(e))
        
        elapsed = time.time() - start_time
        logger.info("restart_source_metrics_complete name=%s elapsed=%.2f", container_name, elapsed)
        return {"success": True, "data": {"status": "running", "elapsed": elapsed}, "error": None}
        
    except Exception as e:
        logger.error("restart_source_metrics_error name=%s error=%s", container_name, str(e))
        return {"success": False, "data": None, "error": "unexpected_error"}