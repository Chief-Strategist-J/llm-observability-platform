from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity
import time
import subprocess
from dataclasses import dataclass
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger

logger = LogQLLogger(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
CERTS_DIR = BASE_DIR / "certs"
COMPOSE_FILE = CONFIG_DIR / "observability-dynamic-docker.yaml"
                                                

@dataclass
class ServiceConfig:
    hostname: str
    ip: str
    port: int
    container_name: str


OBSERVABILITY_SERVICES = {
    "otel": ServiceConfig("scaibu.otel", "172.28.0.10", 8888, "otel-collector"),
    "prometheus": ServiceConfig("scaibu.prometheus", "172.28.0.20", 9090, "prometheus"),
    "loki": ServiceConfig("scaibu.loki", "172.28.0.30", 3100, "loki"),
    "jaeger": ServiceConfig("scaibu.jaeger", "172.28.0.40", 16686, "jaeger"),
    "alertmanager": ServiceConfig("scaibu.alertmanager", "172.28.0.50", 9093, "alertmanager"),
    "grafana": ServiceConfig("scaibu.grafana", "172.28.0.60", 3000, "grafana"),
}


def _truncate_output(text: str, max_length: int = 4000) -> str:
    if len(text) <= max_length:
        return text
    head_length = max_length // 2
    tail_length = max_length - head_length
    return f"{text[:head_length]}\n...\n{text[-tail_length:]}"


def run_command(
    cmd: List[str],
    check: bool = False,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    try:
        completed_process = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logger.debug(
            "command_succeeded",
            command=" ".join(cmd),
            timeout_seconds=timeout,
            stdout=_truncate_output(completed_process.stdout or ""),
            stderr=_truncate_output(completed_process.stderr or ""),
        )
        return completed_process
    except subprocess.TimeoutExpired as e:
        logger.error(
            "command_timeout",
            command=" ".join(cmd),
            timeout_seconds=timeout,
            error=e,
        )
        return subprocess.CompletedProcess(cmd, 1, "", str(e))
    except Exception as e:
        logger.error("command_failed", command=" ".join(cmd), error=e)
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def get_service_hostnames() -> List[str]:
    return [svc.hostname for svc in OBSERVABILITY_SERVICES.values()]


def get_service_entries() -> List[Dict[str, str]]:
    return [{"hostname": svc.hostname, "ip": svc.ip} for svc in OBSERVABILITY_SERVICES.values()]


def get_service_ips() -> Dict[str, str]:
    return {svc.hostname: svc.ip for svc in OBSERVABILITY_SERVICES.values()}


def get_certs_dir() -> Path:
    return CERTS_DIR


def get_config_dir() -> Path:
    return CONFIG_DIR


def get_compose_file() -> Path:
    return COMPOSE_FILE


@activity.defn(name="create_observability_network_activity")
async def create_observability_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "obs-network-create")
    network_name = params.get("network_name", "observability-network")
    subnet = params.get("subnet", "172.28.0.0/16")
    gateway = params.get("gateway", "172.28.0.1")
    
    start_time = time.time()
    
    logger.set_trace_id(trace_id)
    logger.info("create_observability_network_start", network=network_name)
    
    try:
        inspect_result = run_command(["docker", "network", "inspect", network_name], check=False)
        
        if inspect_result.returncode == 0:
            logger.info("network_exists", network=network_name)
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "service": "network-manager",
                "network_name": network_name,
                "created": False,
                "exists": True,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
        
        create_cmd = [
            "docker", "network", "create",
            "--driver", "bridge",
            "--subnet", subnet,
            "--gateway", gateway,
            network_name
        ]
        create_result = run_command(create_cmd, check=False)
        
        if create_result.returncode == 0:
            logger.info("network_created", network=network_name)
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "service": "network-manager",
                "network_name": network_name,
                "created": True,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
        else:
            logger.error("network_creation_failed", network=network_name, error=create_result.stderr)
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "service": "network-manager",
                "network_name": network_name,
                "error": create_result.stderr,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("create_observability_network_failed", error=e)
        return {
            "success": False,
            "service": "network-manager",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }


@activity.defn(name="start_observability_stack_activity")
async def start_observability_stack_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "obs-stack-start")
    compose_file = Path(params.get("compose_file", str(COMPOSE_FILE)))
    timeout_seconds = params.get("timeout_seconds", 300)
    
    start_time = time.time()
    
    logger.set_trace_id(trace_id)
    logger.info("start_observability_stack_begin", compose_file=str(compose_file))
    
    try:
        if not compose_file.exists():
            logger.error("compose_file_not_found", file=str(compose_file))
            return {
                "success": False,
                "service": "stack-manager",
                "error": f"compose_file_not_found: {compose_file}",
                "trace_id": trace_id
            }
        
        cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
        logger.info(
            "stack_start_invoking",
            compose_file=str(compose_file),
            timeout_seconds=timeout_seconds,
        )
        result = run_command(cmd, check=False, timeout=timeout_seconds)

        if result.returncode == 0:
            logger.info("stack_started", compose_file=str(compose_file))
            time.sleep(5)

            ps_cmd = ["docker-compose", "-f", str(compose_file), "ps"]
            ps_result = run_command(ps_cmd, check=False)
            if ps_result.returncode == 0:
                logger.info(
                    "stack_containers_status",
                    compose_file=str(compose_file),
                    status=_truncate_output(ps_result.stdout or ""),
                )
            else:
                logger.warning(
                    "stack_containers_status_failed",
                    compose_file=str(compose_file),
                    stderr=_truncate_output(ps_result.stderr or ""),
                )

            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "service": "stack-manager",
                "containers_status": ps_result.stdout if ps_result.returncode == 0 else "unknown",
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
        else:
            logger.error(
                "stack_start_failed",
                compose_file=str(compose_file),
                stdout=_truncate_output(result.stdout or ""),
                stderr=_truncate_output(result.stderr or ""),
            )
            logs_cmd = [
                "docker-compose",
                "-f",
                str(compose_file),
                "logs",
                "--tail",
                "100",
            ]
            logs_result = run_command(logs_cmd, check=False, timeout=60)
            if logs_result.stdout:
                logger.error(
                    "stack_recent_logs",
                    compose_file=str(compose_file),
                    logs=_truncate_output(logs_result.stdout),
                )
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "service": "stack-manager",
                "error": result.stderr,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("start_observability_stack_failed", error=e)
        return {
            "success": False,
            "service": "stack-manager",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }


@activity.defn(name="stop_observability_stack_activity")
async def stop_observability_stack_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "obs-stack-stop")
    compose_file = Path(params.get("compose_file", str(COMPOSE_FILE)))
    
    start_time = time.time()
    
    logger.set_trace_id(trace_id)
    logger.info("stop_observability_stack_begin", compose_file=str(compose_file))
    
    try:
        if not compose_file.exists():
            logger.warning("compose_file_not_found", file=str(compose_file))
            return {
                "success": True,
                "service": "stack-manager",
                "message": "compose_file_not_found_nothing_to_stop",
                "trace_id": trace_id
            }
        
        cmd = ["docker-compose", "-f", str(compose_file), "down"]
        result = run_command(cmd, check=False)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if result.returncode == 0:
            logger.info("stack_stopped", compose_file=str(compose_file))
            return {
                "success": True,
                "service": "stack-manager",
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
        else:
            logger.error("stack_stop_failed", error=result.stderr)
            return {
                "success": False,
                "service": "stack-manager",
                "error": result.stderr,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("stop_observability_stack_failed", error=e)
        return {
            "success": False,
            "service": "stack-manager",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }


@activity.defn(name="verify_observability_stack_activity")
async def verify_observability_stack_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "obs-stack-verify")
    services = params.get("services", list(OBSERVABILITY_SERVICES.keys()))
    
    start_time = time.time()
    results = {}
    all_healthy = True
    
    logger.set_trace_id(trace_id)
    logger.info("verify_observability_stack_start", services_count=len(services))
    
    try:
        for service_key in services:
            if service_key not in OBSERVABILITY_SERVICES:
                continue
                
            service = OBSERVABILITY_SERVICES[service_key]
            container_name = service.container_name
            
            logger.debug("verifying_container", container=container_name)
            
            inspect_cmd = ["docker", "inspect", "-f", "{{.State.Status}}", container_name]
            result = run_command(inspect_cmd, check=False)
            
            if result.returncode == 0:
                status = result.stdout.strip()
                is_running = status == "running"
                
                results[service_key] = {
                    "container_name": container_name,
                    "status": status,
                    "running": is_running,
                    "hostname": service.hostname,
                    "ip": service.ip,
                    "port": service.port
                }
                
                if not is_running:
                    all_healthy = False
                    logger.warning("container_not_running", container=container_name, status=status)
                else:
                    logger.info("container_running", container=container_name)
            else:
                all_healthy = False
                results[service_key] = {
                    "container_name": container_name,
                    "status": "not_found",
                    "running": False
                }
                logger.error("container_not_found", container=container_name)
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info("verify_observability_stack_complete", all_healthy=all_healthy, duration_ms=duration_ms)
        
        return {
            "success": all_healthy,
            "service": "stack-verifier",
            "results": results,
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("verify_observability_stack_failed", error=e)
        return {
            "success": False,
            "service": "stack-verifier",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }
