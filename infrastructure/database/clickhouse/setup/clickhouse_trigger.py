from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator


clickhouse_config = ServiceConfig(
    compose_file="infrastructure/database/clickhouse/config/docker-compose.yaml",
    hostname="scaibu.clickhouse-ui",
    service_name="clickhouse",
    network_name="database-network",
    ip_address="172.29.0.71",
    port="80",
    subnet="172.29.0.0/16",
    gateway="172.29.0.1",
    health_check_command=["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8123/ping"],
    target_service_for_labels="clickhouse-ui",
    env_vars={}
)


async def setup_clickhouse() -> None:
    orchestrator = ServiceOrchestrator(
        config=clickhouse_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.setup()
    logger.info("event=clickhouse_setup_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


async def teardown_clickhouse() -> None:
    orchestrator = ServiceOrchestrator(
        config=clickhouse_config,
        temporal_host="localhost:7233",
        task_queue="docker-orchestrator-queue"
    )
    result = await orchestrator.teardown()
    logger.info("event=clickhouse_teardown_result success=%s workflow_id=%s", result.get("success"), result.get("workflow_id"))


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if action == "setup":
        asyncio.run(setup_clickhouse())
    elif action == "teardown":
        asyncio.run(teardown_clickhouse())
    else:
        logger.error("Unknown action: %s. Use 'setup' or 'teardown'", action)
        sys.exit(1)
