from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class QdrantSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="qdrant",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.qdrant",
            ip="172.29.0.50"
        )

@activity.defn(name="setup_qdrant_activity")
async def setup_qdrant_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = QdrantSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_qdrant_activity")
async def teardown_qdrant_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = QdrantSetupActivity()
    return await act.teardown_service()
