import logging
from typing import Dict, Any, Optional
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class RedisManager(BaseService):
    SERVICE_NAME = "Redis"
    SERVICE_DESCRIPTION = "in-memory data store"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0, config: Optional[ContainerConfig] = None) -> None:
        if config is None:
            pm = get_port_manager()
            redis_port = pm.get_port("redis", instance_id, "port")

            config = ContainerConfig(
                image="redis:7-alpine",
                name=f"redis-instance-{instance_id}",
                ports={redis_port: redis_port},
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
                    "--databases", "16",
                    "--port", str(redis_port)
                ],
                healthcheck={
                    "test": ["CMD", "redis-cli", "-p", str(redis_port), "ping"],
                    "interval": 30000000000,
                    "timeout": 10000000000,
                    "retries": 3,
                    "start_period": 10000000000
                }
            )

            logger.info(
                "event=redis_manager_init service=redis instance=%s port=%s",
                instance_id, redis_port
            )

        extra_data = {
            "max_memory": "256mb",
            "databases": "16",
            "eviction_policy": "allkeys-lru"
        }

        super().__init__(config=config, extra=extra_data)

    def ping(self) -> bool:
        port = self.config.ports[0][0] if isinstance(self.config.ports, list) else list(self.config.ports.keys())[0]
        code, out = self.exec(f"redis-cli -p {port} ping")
        return code == 0 and "PONG" in out

    def get_info(self) -> str:
        port = list(self.config.ports.keys())[0]
        code, out = self.exec(f"redis-cli -p {port} INFO")
        return out if code == 0 else ""

    def flush_all(self) -> bool:
        port = list(self.config.ports.keys())[0]
        code, out = self.exec(f"redis-cli -p {port} FLUSHALL")
        return code == 0 and "OK" in out


@activity.defn
async def start_redis_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=redis_start params=%s", params)
    RedisManager().run()
    logger.info("event=redis_started")
    return True


@activity.defn
async def stop_redis_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=redis_stop_begin")
    RedisManager().stop(timeout=30)
    logger.info("event=redis_stop_complete")
    return True


@activity.defn
async def restart_redis_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=redis_restart_begin")
    RedisManager().restart()
    logger.info("event=redis_restart_complete")
    return True


@activity.defn
async def delete_redis_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=redis_delete_begin")
    RedisManager().delete(force=False)
    logger.info("event=redis_delete_complete")
    return True
