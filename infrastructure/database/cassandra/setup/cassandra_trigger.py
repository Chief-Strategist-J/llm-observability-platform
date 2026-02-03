from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


cassandra_config = ServiceConfig(
    compose_file="infrastructure/database/cassandra/config/docker-compose.yaml",
    hostname="scaibu.cassandra-web",
    service_name="cassandra",
    network_name="database-network",
    ip_address="172.29.0.91",
    port="3000",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["cqlsh", "-e", "describe keyspaces"],
    target_service_for_labels="cassandra-web",
    env_vars={}
)


async def setup_cassandra() -> None:
    orchestrator = ServiceOrchestrator(
        config=cassandra_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=cassandra_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_cassandra() -> None:
    orchestrator = ServiceOrchestrator(
        config=cassandra_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=cassandra_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_cassandra())
    elif action == "teardown":
        asyncio.run(teardown_cassandra())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
