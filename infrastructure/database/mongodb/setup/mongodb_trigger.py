from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


mongodb_config = ServiceConfig(
    compose_file="infrastructure/database/mongodb/config/docker-compose.yaml",
    hostname="scaibu.mongoexpress",
    service_name="mongodb",
    network_name="database-network",
    ip_address="172.29.0.20",
    port="8081",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["mongosh", "--eval", "db.adminCommand('ping')"],
    env_vars={
        "MONGO_INITDB_ROOT_USERNAME": "admin",
        "MONGO_INITDB_ROOT_PASSWORD": "MongoPassword123!"
    },
    target_service_for_labels="mongoexpress"
)


async def setup_mongodb() -> None:
    orchestrator = ServiceOrchestrator(
        config=mongodb_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=mongodb_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_mongodb() -> None:
    orchestrator = ServiceOrchestrator(
        config=mongodb_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=mongodb_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_mongodb())
    elif action == "teardown":
        asyncio.run(teardown_mongodb())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
