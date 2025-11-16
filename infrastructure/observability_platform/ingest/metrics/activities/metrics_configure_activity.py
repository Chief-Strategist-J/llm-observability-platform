import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def metrics_configure_activity(params: dict) -> dict:
    try:
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [
                        {"targets": ["localhost:9090"]}
                    ]
                }
            ]
        }
        logger.info("Metrics configuration prepared: %s", config)
        return {"success": True, "config": config}
    except Exception as e:
        logger.error("Failed to configure metrics: %s", str(e))
        return {"success": False, "error": str(e)}
