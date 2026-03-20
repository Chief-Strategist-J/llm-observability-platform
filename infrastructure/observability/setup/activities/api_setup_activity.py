import asyncio
import logging
import subprocess
import time
import socket
from pathlib import Path
from typing import Dict, Any, Optional

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

observability_config = ServiceConfig(
    compose_file="infrastructure/observability/setup/config/observability-dynamic-docker.yaml",
    hostname="scaibu.grafana",
    service_name="observability",
    network_name="observability-network",
    ip_address="172.28.0.60",
    port="3000",
    subnet="172.28.0.0/16",
    gateway="172.28.0.1",
    health_check_command=["wget", "--no-verbose", "--tries=1", "--spider", "http://scaibu.grafana/api/health"],
    env_vars={},
    additional_hostnames=[
        "scaibu.prometheus",
        "scaibu.loki", 
        "scaibu.jaeger",
        "scaibu.alertmanager",
        "scaibu.otel"
    ],
    expected_container_name="grafana"
)

def ensure_networks() -> bool:
    network_config = {
        "cicd-network": "172.20.0.0/16",
        "data-network": "172.21.0.0/16",
        "database-network": "172.22.0.0/16",
        "messaging-network": "172.23.0.0/16",
        "observability-network": "172.28.0.0/16",
        "temporal-network": "172.29.0.0/16"
    }
    for network, subnet in network_config.items():
        check_cmd = ["docker", "network", "inspect", network]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            subprocess.run(["docker", "network", "create", "--subnet", subnet, network])
    return True

def check_hostnames() -> bool:
    hostnames = ["scaibu.temporal", "scaibu.otel", "scaibu.observability-api", "scaibu.grafana"]
    missing = []
    for host in hostnames:
        try:
            socket.gethostbyname(host)
        except socket.gaierror:
            missing.append(host)
    
    if missing:
        logger.warning(f"!!! HOSTNAME RESOLUTION FAILED for: {', '.join(missing)} !!!")
        logger.warning("Please run: sudo ./infrastructure/observability/dependencies/configure_hosts.sh --apply")
        return False
    return True

def start_infra_component(compose_rel_path: str) -> bool:
    compose_path = PROJECT_ROOT / compose_rel_path
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
        capture_output=True,
        text=True,
        cwd=str(compose_path.parent)
    )
    if result.returncode != 0:
        logger.error(f"Docker Compose failed for {compose_rel_path}: {result.stderr}")
    return result.returncode == 0

async def setup_observability_api(params: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()
    check_hostnames()
    ensure_networks()
    
    start_infra_component("infrastructure/orchestrator/config/docker/temporal/temporal-orchestrator-compose.yaml")
    time.sleep(5)
    
    subprocess.Popen(
        ["python3", "-m", "infrastructure.orchestrator.base.docker_orchestrator_worker"],
        cwd=str(PROJECT_ROOT)
    )
    time.sleep(2)
    
    start_infra_component("infrastructure/orchestrator/config/docker/traefik/config/traefik-dynamic-docker.yaml")
    time.sleep(5)
    
    orchestrator = ServiceOrchestrator(
        config=observability_config,
        temporal_host="scaibu.temporal:7233",
        task_queue="docker-orchestrator-queue"
    )
    
    result = await orchestrator.setup()
    duration_ms = int((time.time() - start_time) * 1000)
    
    return {
        "success": result.get("success", False),
        "service": "observability",
        "duration_ms": duration_ms,
        "workflow_id": result.get("workflow_id")
    }

async def teardown_observability_api(params: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()
    orchestrator = ServiceOrchestrator(
        config=observability_config,
        temporal_host="scaibu.temporal:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    duration_ms = int((time.time() - start_time) * 1000)
    return {
        "success": result.get("success", False),
        "service": "observability",
        "duration_ms": duration_ms,
        "workflow_id": result.get("workflow_id")
    }
