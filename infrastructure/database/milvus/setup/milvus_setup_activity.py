from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class MilvusSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="milvus",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.milvus",
            ip="172.29.0.100"
        )

@activity.defn(name="setup_milvus_activity")
async def setup_milvus_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MilvusSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_milvus_activity")
async def teardown_milvus_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MilvusSetupActivity()
    return await act.teardown_service()
