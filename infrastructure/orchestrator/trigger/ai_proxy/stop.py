#!/usr/bin/env python3
"""
Simple script to stop Grafana service.
"""

import asyncio
import logging
import sys

if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.activities import stop_grafana_container

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def stop_grafana_service() -> bool:
    logger.info("Stopping Grafana container...")
    success = await stop_grafana_container("grafana")
    return success


async def stop_specific_workflow(workflow_id: str) -> bool:
    logger.info(f"Stopping Grafana workflow: {workflow_id}")
    return await stop_grafana_service()


async def main():
    logger.info("=" * 60)
    logger.info("🔄 STOPPING GRAFANA SERVICE")
    logger.info("=" * 60)

    if len(sys.argv) > 1:
        workflow_id = sys.argv[1]
        success = await stop_specific_workflow(workflow_id)
    else:
        success = await stop_grafana_service()

    if success:
        logger.info("=" * 60)
        logger.info("✅ Grafana stopped successfully!")
        logger.info("📋 Check 'docker ps' to verify cleanup")
    else:
        logger.error("=" * 60)
        logger.error("❌ Failed to stop Grafana")
        logger.error("📋 Grafana container may still be running")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
