from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


neo4j_config = ServiceConfig(
    compose_file="infrastructure/database/neo4j/config/docker-compose.yaml",
    hostname="scaibu.neo4j",
    service_name="neo4j",
    network_name="database-network",
    ip_address="172.29.0.40",
    port="7474",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["cypher-shell", "-u", "neo4j", "-p", "Neo4jPassword123!", "RETURN 1"],
    target_service_for_labels="neo4j",
    env_vars={}
)


async def setup_neo4j() -> None:
    orchestrator = ServiceOrchestrator(
        config=neo4j_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=neo4j_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_neo4j() -> None:
    orchestrator = ServiceOrchestrator(
        config=neo4j_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=neo4j_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_neo4j())
    elif action == "teardown":
        asyncio.run(teardown_neo4j())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
