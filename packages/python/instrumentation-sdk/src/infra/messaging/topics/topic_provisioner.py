import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from kafka.admin import KafkaAdminClient, NewTopic
from ..broker.broker_config import kafka_broker_config

sdk_root = Path(__file__).resolve().parents[4]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

class TopicProvisioner:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.bootstrap_servers = bootstrap_servers or kafka_broker_config.bootstrap_servers

    def load_contract_topics(self) -> List[Dict[str, Any]]:
        topics_yaml_path = sdk_root / "contracts" / "registries" / "topics.yaml"
        if not topics_yaml_path.exists():
            return []
        with open(topics_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("topics", [])

    def provision_topics(self, topic_specs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
        specs = topic_specs if topic_specs is not None else self.load_contract_topics()
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id="instrumentation-sdk-topic-provisioner"
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

                new_topics.append(NewTopic(
                    name=name,
                    num_partitions=spec.get("partitions", 3),
                    replication_factor=spec.get("replication_factor", 1),
                    topic_configs={"cleanup.policy": spec.get("cleanup_policy", "delete")}
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
