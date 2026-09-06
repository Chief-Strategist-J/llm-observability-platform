from typing import Dict, Any, List, Optional
from ..migrations.kafka_topic_migration import KafkaTopicMigrationEngine

class TopicProvisioner:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.migration_engine = KafkaTopicMigrationEngine(bootstrap_servers=bootstrap_servers)

    def provision_topics(self) -> Dict[str, str]:
        return self.migration_engine.apply_migrations()

    def rollback_topics(self, topic_names: Optional[List[str]] = None) -> Dict[str, str]:
        return self.migration_engine.rollback_migrations(topic_names=topic_names)

    def resolve_event_topic(self, event_name: str) -> Optional[str]:
        return self.migration_engine.get_topic_for_event(event_name)
