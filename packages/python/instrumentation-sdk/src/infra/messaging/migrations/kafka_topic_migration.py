import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from kafka.admin import KafkaAdminClient, NewTopic
from ..broker.broker_config import kafka_broker_config

sdk_root = Path(__file__).resolve().parents[4]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

from config.kafka.kafka_topic_constants import topic_constants

class KafkaTopicMigrationEngine:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.bootstrap_servers = bootstrap_servers or kafka_broker_config.bootstrap_servers

    def load_contract_events(self) -> List[Dict[str, Any]]:
        events_yaml_path = sdk_root / "contracts" / "registries" / "events.yaml"
        if not events_yaml_path.exists():
            return []
        with open(events_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("events", [])

    def load_contract_topics(self) -> List[Dict[str, Any]]:
        topics_yaml_path = sdk_root / "contracts" / "registries" / "topics.yaml"
        if not topics_yaml_path.exists():
            return []
        with open(topics_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("topics", [])

    def get_topic_for_event(self, event_name: str) -> Optional[str]:
        events = self.load_contract_events()
        for ev in events:
            if ev.get("name") == event_name:
                return ev.get("topic")
        return None

    def apply_migrations(self) -> Dict[str, str]:
        specs = self.load_contract_topics()
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id=topic_constants.CLIENT_ID,
            api_version=(3, 7, 0),
            api_version_auto_timeout_ms=5000
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

    def rollback_migrations(self, topic_names: Optional[List[str]] = None) -> Dict[str, str]:
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id=topic_constants.CLIENT_ID,
            api_version=(3, 7, 0)
        )
        results = {}
        target_topics = topic_names or [t["name"] for t in self.load_contract_topics()]

        try:
            admin_client.delete_topics(topics=target_topics)
            for t in target_topics:
                results[t] = "deleted"
        except Exception as e:
            results["error"] = str(e)
        finally:
            admin_client.close()

        return results
