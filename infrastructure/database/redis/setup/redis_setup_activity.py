from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG


class RedisSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        config = DATABASE_CONFIG.get("redis", {})
        super().__init__(
            service_name="redis",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname=config.get("ui_hostname", "scaibu.redis"),
            ip=config.get("container_ip", "172.29.0.30")
        )


@activity.defn(name="setup_redis_activity")
async def setup_redis_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = RedisSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))


@activity.defn(name="teardown_redis_activity")
async def teardown_redis_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = RedisSetupActivity()
    return await act.teardown_service()
