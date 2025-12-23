import subprocess
import time
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.logql_logger import LogQLLogger


@activity.defn(name="check_docker_connectivity_activity")
async def check_docker_connectivity_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", f"docker-check-{int(time.time())}")
    log = LogQLLogger(__name__)
    log.set_trace_id(trace_id)
    
    log.info("docker_connectivity_check_start", trace_id=trace_id)
    
    start_time = time.time()
    results = {}
    
    log.info("checking_docker_daemon", trace_id=trace_id)
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        docker_running = result.returncode == 0
        results["docker_daemon"] = {
            "running": docker_running,
            "info": result.stdout[:500] if docker_running else result.stderr[:500]
        }
        
        log.info(
            "docker_daemon_check_complete",
            trace_id=trace_id,
            running=docker_running
        )
        
    except Exception as e:
        results["docker_daemon"] = {
            "running": False,
            "error": str(e)
        }
        log.error("docker_daemon_check_failed", error=e, trace_id=trace_id)
    
    log.info("checking_docker_registry_connectivity", trace_id=trace_id)
    try:
        result = subprocess.run(
            ["docker", "pull", "hello-world"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        
        registry_accessible = result.returncode == 0
        results["docker_registry"] = {
            "accessible": registry_accessible,
            "info": result.stdout[:500] if registry_accessible else result.stderr[:500]
        }
        
        log.info(
            "docker_registry_check_complete",
            trace_id=trace_id,
            accessible=registry_accessible
        )
        
        if registry_accessible:
            subprocess.run(
                ["docker", "rmi", "hello-world"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
    except Exception as e:
        results["docker_registry"] = {
            "accessible": False,
            "error": str(e)
        }
        log.error("docker_registry_check_failed", error=e, trace_id=trace_id)
    
    log.info("checking_docker_networks", trace_id=trace_id)
    try:
        result = subprocess.run(
            ["docker", "network", "ls"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        networks_ok = result.returncode == 0
        results["docker_networks"] = {
            "ok": networks_ok,
            "networks": result.stdout if networks_ok else result.stderr
        }
        
        log.info(
            "docker_networks_check_complete",
            trace_id=trace_id,
            ok=networks_ok
        )
        
    except Exception as e:
        results["docker_networks"] = {
            "ok": False,
            "error": str(e)
        }
        log.error("docker_networks_check_failed", error=e, trace_id=trace_id)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    all_ok = (
        results.get("docker_daemon", {}).get("running", False) and
        results.get("docker_registry", {}).get("accessible", False) and
        results.get("docker_networks", {}).get("ok", False)
    )
    
    log.info(
        "docker_connectivity_check_complete",
        trace_id=trace_id,
        all_ok=all_ok,
        duration_ms=duration_ms
    )
    
    return {
        "success": all_ok,
        "trace_id": trace_id,
        "duration_ms": duration_ms,
        "results": results
    }