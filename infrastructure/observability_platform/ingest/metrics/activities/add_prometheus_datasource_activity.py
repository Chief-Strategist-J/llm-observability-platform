import logging
from temporalio import activity
from infrastructure.observability_platform.shared.api.grafana_client import GrafanaClient

logger = logging.getLogger(__name__)


@activity.defn
async def add_prometheus_datasource_activity(params: dict) -> dict:
    client = GrafanaClient()
    payload = {
        "name": "prometheus-development",
        "type": "prometheus",
        "url": "http://prometheus-development:9090",
        "access": "proxy"
    }
    try:
        result = client.add_datasource(payload)
        logger.info(result)
        return result
    except Exception as e:
        logger.error(e)
        return {"error": str(e)}
