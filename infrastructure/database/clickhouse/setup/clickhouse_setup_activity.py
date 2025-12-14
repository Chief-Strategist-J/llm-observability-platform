from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class ClickhouseSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="clickhouse",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.clickhouse",
            ip="172.29.0.70"
        )

@activity.defn(name="setup_clickhouse_activity")
async def setup_clickhouse_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ClickhouseSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_clickhouse_activity")
async def teardown_clickhouse_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ClickhouseSetupActivity()
    return await act.teardown_service()
