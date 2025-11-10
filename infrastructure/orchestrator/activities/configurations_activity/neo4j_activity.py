import logging
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class Neo4jManager(BaseService):
    SERVICE_NAME = "Neo4j"
    SERVICE_DESCRIPTION = "graph database"
    DEFAULT_PORT = 7474
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        config = ContainerConfig(
            image="neo4j:latest",
            name="neo4j-development",
            ports={
                7474: 7474,
                7687: 7687,
            },
            volumes={
                "neo4j-data": "/data",
                "neo4j-logs": "/logs",
                "neo4j-import": "/var/lib/neo4j/import",
                "neo4j-plugins": "/plugins",
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
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:7474 || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 60000000000
            }
        )
        super().__init__(config)

    def execute_cypher(self, query: str) -> str:
        cmd = f'cypher-shell -u neo4j -p Neo4jPassword123! "{query}"'
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to execute Cypher query: %s", out)
            return ""
        return out


@activity.defn
async def start_neo4j_activity(params: Dict[str, Any]) -> bool:
    manager = Neo4jManager()
    manager.run()
    return True


@activity.defn
async def stop_neo4j_activity(params: Dict[str, Any]) -> bool:
    manager = Neo4jManager()
    manager.stop(timeout=30)
    return True


@activity.defn
async def restart_neo4j_activity(params: Dict[str, Any]) -> bool:
    manager = Neo4jManager()
    manager.restart()
    return True


@activity.defn
async def delete_neo4j_activity(params: Dict[str, Any]) -> bool:
    manager = Neo4jManager()
    manager.delete(force=False)
    return True
