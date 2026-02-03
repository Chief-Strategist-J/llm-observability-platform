from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


apicurio_config = ServiceConfig(
    compose_file="infrastructure/database/apicurio/config/docker-compose.yaml",
    hostname="scaibu.apicurio",
    service_name="apicurio-registry",
    network_name="database-network",
    ip_address="172.29.0.50",
    port="8080",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["curl", "-f", "http://localhost:8080/health/ready"],
    target_service_for_labels="apicurio-registry",
    env_vars={}
)


async def setup_apicurio() -> None:
    logger.info("event=apicurio_setup_start")
    orchestrator = ServiceOrchestrator(
        config=apicurio_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=apicurio_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_apicurio() -> None:
    logger.info("event=apicurio_teardown_start")
    orchestrator = ServiceOrchestrator(
        config=apicurio_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=apicurio_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_apicurio())
    elif action == "teardown":
        asyncio.run(teardown_apicurio())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
