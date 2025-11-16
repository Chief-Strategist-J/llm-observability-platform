import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def collect_and_ship_metrics_activity(params: dict) -> dict:
    try:
        metrics_config = {
            "collection_interval": "15s",
            "batch_size": 100,
            "export_timeout": "30s",
            "exporters": ["prometheus", "otlp"]
        }
        logger.info("Metrics collection and shipping configured: %s", metrics_config)
        return {"success": True, "config": metrics_config}
    except Exception as e:
        logger.error("Failed to configure metrics collection: %s", str(e))
        return {"success": False, "error": str(e)}
