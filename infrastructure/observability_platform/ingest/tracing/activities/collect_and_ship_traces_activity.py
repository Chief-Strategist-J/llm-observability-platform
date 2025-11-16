import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def collect_and_ship_traces_activity(params: dict) -> dict:
    try:
        traces_config = {
            "collection_interval": "5s",
            "batch_size": 512,
            "export_timeout": "30s",
            "exporters": ["jaeger", "otlp"],
            "processors": ["batch", "memory_limiter"]
        }
        logger.info("Traces collection and shipping configured: %s", traces_config)
        return {"success": True, "config": traces_config}
    except Exception as e:
        logger.error("Failed to configure traces collection: %s", str(e))
        return {"success": False, "error": str(e)}
