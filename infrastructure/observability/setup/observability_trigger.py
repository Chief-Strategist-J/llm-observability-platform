from __future__ import annotations

import asyncio
import logging
from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


observability_config = ServiceConfig(
    compose_file="infrastructure/observability/setup/config/observability-dynamic-docker.yaml",
    hostname="scaibu.grafana",  # Primary entry point
    service_name="observability",
    network_name="observability-network",
    ip_address="172.28.0.60",  # IP for Grafana (or main service)
    port="3000",
    subnet="172.28.0.0/16",
    gateway="172.28.0.1",
    health_check_command=["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"],  # Check Grafana
    env_vars={},
    additional_hostnames=[
        "scaibu.prometheus",
        "scaibu.loki", 
        "scaibu.jaeger",
        "scaibu.alertmanager",
        "scaibu.otel"
    ],
    expected_container_name="grafana"  # The stack names container 'grafana' explicitly
)


async def setup() -> None:
    orchestrator = ServiceOrchestrator(
        config=observability_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=observability_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown() -> None:
    orchestrator = ServiceOrchestrator(
        config=observability_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=observability_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup())
    elif action == "teardown":
        asyncio.run(teardown())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
