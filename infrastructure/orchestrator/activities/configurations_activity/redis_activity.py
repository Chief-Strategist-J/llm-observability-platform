import logging
from typing import Optional
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
        exit_code, output = self.exec("redis-cli ping")
        return exit_code == 0 and "PONG" in output

    def get_info(self) -> str:
        exit_code, output = self.exec("redis-cli INFO")
        return output if exit_code == 0 else ""

    def flush_all(self) -> bool:
        exit_code, output = self.exec("redis-cli FLUSHALL")
        return exit_code == 0 and "OK" in output


@activity.defn
async def start_redis_activity(service_name: str) -> bool:
    try:
        manager = RedisManager()
        manager.run()
        return True
    except Exception as e:
        logger.error("Failed to start Redis service: %s", str(e), exc_info=True)
        return False


@activity.defn
async def stop_redis_activity(service_name: str) -> bool:
    try:
        manager = RedisManager()
        manager.stop(timeout=30)
        return True
    except Exception as e:
        logger.error("Failed to stop Redis service: %s", str(e), exc_info=True)
        return False


@activity.defn
async def restart_redis_activity(service_name: str) -> bool:
    try:
        manager = RedisManager()
        manager.restart()
        return True
    except Exception as e:
        logger.error("Failed to restart Redis service: %s", str(e), exc_info=True)
        return False


@activity.defn
async def delete_redis_activity(service_name: str, force: bool = False) -> bool:
    try:
        manager = RedisManager()
        manager.delete(force=force)
        return True
    except Exception as e:
        logger.error("Failed to delete Redis service: %s", str(e), exc_info=True)
        return False
