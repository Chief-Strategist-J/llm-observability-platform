from temporalio import activity
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import FileConfigStore
from infrastructure.observability_platform.ingest.application_stdout.service.log_discovery_service import LocalLogDiscoveryService

CONFIG_PATH = "infrastructure/observability_platform/ingest/config/log_discovery_config.yaml"


@activity.defn
async def discover_log_files_activity(params: dict) -> list:
    store = FileConfigStore(CONFIG_PATH)
    config = store.ensure_exists()
    service = LocalLogDiscoveryService(config)
    return service.discover()
