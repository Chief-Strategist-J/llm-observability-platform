from pathlib import Path
from temporalio import activity
from typing import Dict, Any

from infrastructure.database.shared.base_database_setup import BaseDatabaseSetupActivity

class Neo4jSetupActivity(BaseDatabaseSetupActivity):
    def __init__(self):
        super().__init__(
            service_name="neo4j",
            compose_file=str(Path(__file__).parent.parent / "config" / "docker-compose.yaml"),
            hostname="scaibu.neo4j",
            ip="172.29.0.40"
        )

@activity.defn(name="setup_neo4j_activity")
async def setup_neo4j_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = Neo4jSetupActivity()
    return await act.setup_service(env_vars=params.get("env_vars", {}))

@activity.defn(name="teardown_neo4j_activity")
async def teardown_neo4j_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    act = Neo4jSetupActivity()
    return await act.teardown_service()
