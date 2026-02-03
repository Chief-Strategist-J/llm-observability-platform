from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


chroma_config = ServiceConfig(
    compose_file="infrastructure/database/chroma/config/docker-compose.yaml",
    hostname="scaibu.chroma",
    service_name="chroma",
    network_name="database-network",
    ip_address="172.29.0.120",
    port="8000",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["curl", "-f", "http://localhost:8000/api/v1/heartbeat"],
    target_service_for_labels="chroma",
    env_vars={}
)


async def setup_chroma() -> None:
    orchestrator = ServiceOrchestrator(
        config=chroma_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=chroma_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_chroma() -> None:
    orchestrator = ServiceOrchestrator(
        config=chroma_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=chroma_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_chroma())
    elif action == "teardown":
        asyncio.run(teardown_chroma())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
