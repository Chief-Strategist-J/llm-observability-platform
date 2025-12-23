from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG


class ClickhouseSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        config = DATABASE_CONFIG.get("clickhouse", {})
        super().__init__(
            service_name="clickhouse",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname=config.get("ui_hostname", "scaibu.clickhouse"),
            ip=config.get("container_ip", "172.29.0.70")
        )


@activity.defn(name="setup_clickhouse_activity")
async def setup_clickhouse_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ClickhouseSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_clickhouse_activity")
async def teardown_clickhouse_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ClickhouseSetupActivity()
    return await act.teardown_service()
