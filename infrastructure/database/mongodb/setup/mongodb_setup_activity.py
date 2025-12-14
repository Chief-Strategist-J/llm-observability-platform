from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity


class MongodbSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="mongodb",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.mongodb",
            ip="172.29.0.20"
        )

@activity.defn(name="setup_mongodb_activity")
async def setup_mongodb_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MongodbSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_mongodb_activity")
async def teardown_mongodb_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MongodbSetupActivity()
    return await act.teardown_service()
