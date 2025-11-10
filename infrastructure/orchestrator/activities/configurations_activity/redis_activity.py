import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class RedisManager(BaseService):
    SERVICE_NAME = "Redis"
    SERVICE_DESCRIPTION = "in-memory data store"
    DEFAULT_PORT = 6379
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, config: Optional[ContainerConfig] = None) -> None:
        if config is None:
            config = ContainerConfig(
                image="redis:7-alpine",
                name="redis-development",
                ports={6379: 6379},
                volumes={"redis-data": "/data"},
                network="observability-network",
                memory="256m",
                memory_reservation="128m",
                cpus=0.5,
                restart="unless-stopped",
                environment={
                    "REDIS_PASSWORD": "",
                    "REDIS_DATABASES": "16",
                    "REDIS_MAXMEMORY": "256mb",
                    "REDIS_MAXMEMORY_POLICY": "allkeys-lru",
                },
                command=[
                    "redis-server",
                    "--maxmemory", "256mb",
                    "--maxmemory-policy", "allkeys-lru",
                    "--databases", "16"
                ],
                healthcheck={
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 3,
                    "start_period": 10000000000
                }
            )
        extra_data = {
            "max_memory": "256mb",
            "databases": "16",
            "eviction_policy": "allkeys-lru"
        }
        super().__init__(config=config, extra=extra_data)

    def ping(self) -> bool:
        code, out = self.exec("redis-cli ping")
        return code == 0 and "PONG" in out

    def get_info(self) -> str:
        code, out = self.exec("redis-cli INFO")
        return out if code == 0 else ""

    def flush_all(self) -> bool:
        code, out = self.exec("redis-cli FLUSHALL")
        return code == 0 and "OK" in out


@activity.defn
async def start_redis_activity(params: Dict[str, Any]) -> bool:
    RedisManager().run()
    return True


@activity.defn
async def stop_redis_activity(params: Dict[str, Any]) -> bool:
    RedisManager().stop(timeout=30)
    return True


@activity.defn
async def restart_redis_activity(params: Dict[str, Any]) -> bool:
    RedisManager().restart()
    return True


@activity.defn
async def delete_redis_activity(params: Dict[str, Any]) -> bool:
    RedisManager().delete(force=False)
    return True
