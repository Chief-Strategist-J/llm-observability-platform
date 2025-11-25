import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class Neo4jManager(BaseService):
    SERVICE_NAME = "Neo4j"
    SERVICE_DESCRIPTION = "graph database"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        http_port = pm.get_port("neo4j", instance_id, "http_port")
        bolt_port = pm.get_port("neo4j", instance_id, "bolt_port")

        config = ContainerConfig(
            image="neo4j:latest",
            name=f"neo4j-instance-{instance_id}",
            ports={
                http_port: http_port,
                bolt_port: bolt_port
            },
            volumes={
                f"neo4j-data-{instance_id}": "/data",
                f"neo4j-logs-{instance_id}": "/logs",
                f"neo4j-import-{instance_id}": "/var/lib/neo4j/import",
                f"neo4j-plugins-{instance_id}": "/plugins"
            },
            network="data-network",
            memory="1g",
            memory_reservation="512m",
            cpus=1.0,
            restart="unless-stopped",
            environment={
                "NEO4J_AUTH": "neo4j/Neo4jPassword123!",
                "NEO4J_ACCEPT_LICENSE_AGREEMENT": "yes",
                "NEO4J_dbms_memory_pagecache_size": "512M",
                "NEO4J_dbms_memory_heap_initial__size": "512M",
                "NEO4J_dbms_memory_heap_max__size": "512M",
                "NEO4J_dbms_connector_bolt_listen__address": f"0.0.0.0:{bolt_port}",
                "NEO4J_dbms_connector_http_listen__address": f"0.0.0.0:{http_port}"
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{http_port} || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 60000000000
            }
        )

        logger.info(
            "event=neo4j_manager_init instance=%s http_port=%s bolt_port=%s",
            instance_id, http_port, bolt_port
        )

        extra = {
            "http_port": http_port,
            "bolt_port": bolt_port,
            "instance_id": instance_id
        }

        super().__init__(config, extra)

        logger.info(
            "event=neo4j_manager_initialized instance=%s container=%s image=%s http=%s bolt=%s",
            instance_id, config.name, config.image, http_port, bolt_port
        )

    def execute_cypher(self, query: str) -> str:
        bolt_port = self.extra.get("bolt_port")
        cmd = f'cypher-shell -u neo4j -p Neo4jPassword123! -a bolt://localhost:{bolt_port} "{query}"'
        code, out = self.exec(cmd)

        if code != 0:
            logger.error(
                "event=neo4j_execute_cypher_failed instance=%s port=%s output=%s",
                self.extra.get("instance_id"), bolt_port, out
            )
            return ""

        logger.info(
            "event=neo4j_execute_cypher_success instance=%s",
            self.extra.get("instance_id")
        )

        return out


@activity.defn
async def start_neo4j_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=neo4j_start params=%s", params)
    manager = Neo4jManager()
    manager.run()
    logger.info("event=neo4j_started")
    return True


@activity.defn
async def stop_neo4j_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=neo4j_stop")
    manager = Neo4jManager()
    manager.stop(timeout=30)
    logger.info("event=neo4j_stopped")
    return True


@activity.defn
async def restart_neo4j_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=neo4j_restart")
    manager = Neo4jManager()
    manager.restart()
    logger.info("event=neo4j_restarted")
    return True


@activity.defn
async def delete_neo4j_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=neo4j_delete")
    manager = Neo4jManager()
    manager.delete(force=False)
    logger.info("event=neo4j_deleted")
    return True
