import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def tracing_configure_activity(params: dict) -> dict:
    try:
        config = {
            "sampler": {
                "type": "probabilistic",
                "param": 1
            },
            "reporter_loggers": True,
            "local_agent": {
                "reporting_host": "jaeger-development",
                "reporting_port": 6831
            }
        }
        logger.info("Tracing configuration prepared: %s", config)
        return {"success": True, "config": config}
    except Exception as e:
        logger.error("Failed to configure tracing: %s", str(e))
        return {"success": False, "error": str(e)}
