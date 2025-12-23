from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG


class PostgresSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        config = DATABASE_CONFIG.get("postgres", {})
        super().__init__(
            service_name="postgres",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname=config.get("ui_hostname", "scaibu.pgadmin"),
            ip=config.get("container_ip", "172.29.0.10")
        )


@activity.defn(name="setup_postgres_activity")
async def setup_postgres_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = PostgresSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_postgres_activity")
async def teardown_postgres_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = PostgresSetupActivity()
    return await act.teardown_service()
