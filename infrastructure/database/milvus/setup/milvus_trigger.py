from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


milvus_config = ServiceConfig(
    compose_file="infrastructure/database/milvus/config/docker-compose.yaml",
    hostname="scaibu.attu",
    service_name="milvus",
    network_name="database-network",
    ip_address="172.29.0.101",
    port="3000",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["curl", "-f", "http://localhost:9091/healthz"],
    target_service_for_labels="attu",
    env_vars={}
)


async def setup_milvus() -> None:
    orchestrator = ServiceOrchestrator(
        config=milvus_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=milvus_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_milvus() -> None:
    orchestrator = ServiceOrchestrator(
        config=milvus_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=milvus_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_milvus())
    elif action == "teardown":
        asyncio.run(teardown_milvus())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
