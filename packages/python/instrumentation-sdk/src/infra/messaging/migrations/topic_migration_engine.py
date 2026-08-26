import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from kafka.admin import KafkaAdminClient, NewTopic
from ..broker.broker_config import kafka_broker_config

sdk_root = Path(__file__).resolve().parents[4]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

from config.kafka.kafka_topic_constants import topic_constants

class TopicMigrationEngine:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.bootstrap_servers = bootstrap_servers or kafka_broker_config.bootstrap_servers
        self.topics_dir = sdk_root / "database" / "kafka-topics"

    def load_migration_files(self) -> List[Dict[str, Any]]:
        if not self.topics_dir.exists():
            return []
        migration_files = sorted(list(self.topics_dir.glob("*[0-9].json")))
        specs = []
        for file_path in migration_files:
            with open(file_path, "r", encoding="utf-8") as f:
                specs.append(json.load(f))
        return specs

    def apply_migrations(self) -> Dict[str, str]:
        specs = self.load_migration_files()
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id=topic_constants.CLIENT_ID
        )
        results = {}
        new_topics = []

        try:
            existing_topics = set(admin_client.list_topics())
            for spec in specs:
                name = spec["name"]
                if name in existing_topics:
                    results[name] = "exists"
                    continue

                configs = {
                    "cleanup.policy": spec.get("cleanup_policy", topic_constants.DEFAULT_CLEANUP_POLICY),
                    "retention.ms": str(spec.get("retention_ms", topic_constants.DEFAULT_RETENTION_MS)),
                    "min.insync.replicas": str(spec.get("min_insync_replicas", topic_constants.DEFAULT_MIN_INSYNC_REPLICAS))
                }

                new_topics.append(NewTopic(
                    name=name,
                    num_partitions=spec.get("partitions", topic_constants.DEFAULT_PARTITIONS),
                    replication_factor=spec.get("replication_factor", topic_constants.DEFAULT_REPLICATION_FACTOR),
                    topic_configs=configs
                ))

            if new_topics:
                admin_client.create_topics(new_topics=new_topics, validate_only=False)
                for t in new_topics:
                    results[t.name] = "created"

        except Exception as e:
            results["error"] = str(e)
        finally:
            admin_client.close()

        return results
