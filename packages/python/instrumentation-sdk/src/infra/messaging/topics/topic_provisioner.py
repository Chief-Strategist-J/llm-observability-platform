from typing import Dict, Any, List, Optional
from ..migrations.topic_migration_engine import TopicMigrationEngine

class TopicProvisioner:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self._engine = TopicMigrationEngine(bootstrap_servers=bootstrap_servers)

    def provision_topics(self, topic_specs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
        return self._engine.apply_migrations()
