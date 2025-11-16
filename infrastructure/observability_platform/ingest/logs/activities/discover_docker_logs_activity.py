from temporalio import activity
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import FileConfigStore
from infrastructure.observability_platform.ingest.application_stdout.service.docker_log_discovery_service import DockerLogDiscoveryService

CONFIG_PATH = "infrastructure/observability_platform/ingest/config/log_discovery_config.yaml"

@activity.defn
async def discover_docker_logs_activity(params: dict) -> list:
    store = FileConfigStore(CONFIG_PATH)
    config = store.ensure_exists()
    service = DockerLogDiscoveryService(config)
    return service.discover()
