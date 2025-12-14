from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class WeaviateSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="weaviate",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.weaviate",
            ip="172.29.0.110"
        )

@activity.defn(name="setup_weaviate_activity")
async def setup_weaviate_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = WeaviateSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_weaviate_activity")
async def teardown_weaviate_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = WeaviateSetupActivity()
    return await act.teardown_service()
