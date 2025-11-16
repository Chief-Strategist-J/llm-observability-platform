import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def discover_metrics_sources_activity(params: dict) -> dict:
    try:
        sources = [
            {
                "name": "prometheus",
                "type": "prometheus",
                "url": "http://prometheus-development:9090",
                "enabled": True
            },
            {
                "name": "node-exporter",
                "type": "node",
                "url": "http://localhost:9100",
                "enabled": True
            }
        ]
        logger.info("Discovered %d metrics sources", len(sources))
        return {"success": True, "sources": sources}
    except Exception as e:
        logger.error("Failed to discover metrics sources: %s", str(e))
        return {"success": False, "error": str(e)}
