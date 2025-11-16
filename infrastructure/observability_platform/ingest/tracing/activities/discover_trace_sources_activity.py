import logging
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def discover_trace_sources_activity(params: dict) -> dict:
    try:
        sources = [
            {
                "name": "jaeger",
                "type": "jaeger",
                "url": "http://jaeger-development:16686",
                "enabled": True
            },
            {
                "name": "otel-collector",
                "type": "otlp",
                "url": "http://otel-collector:4317",
                "enabled": True
            }
        ]
        logger.info("Discovered %d trace sources", len(sources))
        return {"success": True, "sources": sources}
    except Exception as e:
        logger.error("Failed to discover trace sources: %s", str(e))
        return {"success": False, "error": str(e)}
