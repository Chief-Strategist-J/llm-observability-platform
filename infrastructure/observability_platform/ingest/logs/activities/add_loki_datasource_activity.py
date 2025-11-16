import logging
from temporalio import activity
from infrastructure.observability_platform.shared.api.grafana_client import GrafanaClient

logger = logging.getLogger(__name__)


@activity.defn
async def add_loki_datasource_activity(params: dict) -> dict:
    client = GrafanaClient()
    payload = {
        "name": "loki-development",
        "type": "loki",
        "url": "http://loki-development:3100",
        "access": "proxy"
    }
    try:
        result = client.add_datasource(payload)
        logger.info(result)
        return result
    except Exception as e:
        logger.error(e)
        return {"error": str(e)}
