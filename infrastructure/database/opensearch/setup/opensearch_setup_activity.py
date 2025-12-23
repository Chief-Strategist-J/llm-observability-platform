from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG


class OpensearchSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        config = DATABASE_CONFIG.get("opensearch", {})
        super().__init__(
            service_name="opensearch",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname=config.get("ui_hostname", "scaibu.opensearch-dashboards"),
            ip=config.get("container_ip", "172.29.0.80")
        )


@activity.defn(name="setup_opensearch_activity")
async def setup_opensearch_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = OpensearchSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_opensearch_activity")
async def teardown_opensearch_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = OpensearchSetupActivity()
    return await act.teardown_service()
