from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class MinioSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="minio",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.minio",
            ip="172.29.0.60"
        )

@activity.defn(name="setup_minio_activity")
async def setup_minio_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MinioSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_minio_activity")
async def teardown_minio_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = MinioSetupActivity()
    return await act.teardown_service()
