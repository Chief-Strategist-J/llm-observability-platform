from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class CassandraSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="cassandra",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.cassandra",
            ip="172.29.0.90"
        )

@activity.defn(name="setup_cassandra_activity")
async def setup_cassandra_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = CassandraSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_cassandra_activity")
async def teardown_cassandra_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = CassandraSetupActivity()
    return await act.teardown_service()
