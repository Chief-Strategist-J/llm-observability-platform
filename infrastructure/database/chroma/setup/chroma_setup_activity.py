from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG


class ChromaSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        config = DATABASE_CONFIG.get("chroma", {})
        super().__init__(
            service_name="chroma",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname=config.get("ui_hostname", "scaibu.chroma"),
            ip=config.get("container_ip", "172.29.0.120")
        )


@activity.defn(name="setup_chroma_activity")
async def setup_chroma_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ChromaSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_chroma_activity")
async def teardown_chroma_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = ChromaSetupActivity()
    return await act.teardown_service()
