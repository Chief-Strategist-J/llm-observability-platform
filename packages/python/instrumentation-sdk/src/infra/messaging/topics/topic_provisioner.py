import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from kafka.admin import KafkaAdminClient, NewTopic
from ..broker.broker_config import kafka_broker_config
from config.kafka.kafka_topic_constants import topic_constants

sdk_root = Path(__file__).resolve().parents[4]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

class TopicManager:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.bootstrap_servers = bootstrap_servers or kafka_broker_config.bootstrap_servers

    def load_contract_topics(self) -> List[Dict[str, Any]]:
        topics_yaml_path = sdk_root / "contracts" / "registries" / "topics.yaml"
        if not topics_yaml_path.exists():
            return []
        with open(topics_yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("topics", [])

    def create_topic(self, name: str, partitions: Optional[int] = None, replication_factor: Optional[int] = None, configs: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id=topic_constants.CLIENT_ID
        )
        try:
            existing_topics = set(admin_client.list_topics())
            if name in existing_topics:
                return {name: "exists"}

            topic_configs = configs or {
                "cleanup.policy": topic_constants.DEFAULT_CLEANUP_POLICY,
                "retention.ms": str(topic_constants.DEFAULT_RETENTION_MS),
                "min.insync.replicas": str(topic_constants.DEFAULT_MIN_INSYNC_REPLICAS)
            }

            new_topic = NewTopic(
                name=name,
                num_partitions=partitions or topic_constants.DEFAULT_PARTITIONS,
                replication_factor=replication_factor or topic_constants.DEFAULT_REPLICATION_FACTOR,
                topic_configs=topic_configs
            )
            admin_client.create_topics(new_topics=[new_topic], validate_only=False)
            return {name: "created"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            admin_client.close()

    def provision_all_topics(self) -> Dict[str, str]:
        specs = self.load_contract_topics()
        results = {}
        for spec in specs:
            name = spec["name"]
            res = self.create_topic(
                name=name,
                partitions=spec.get("partitions"),
                replication_factor=spec.get("replication_factor"),
                configs={"cleanup.policy": spec.get("cleanup_policy", topic_constants.DEFAULT_CLEANUP_POLICY)}
            )
            results.update(res)
        return results

    def delete_topic(self, name: str) -> Dict[str, str]:
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id=topic_constants.CLIENT_ID
        )
        try:
            admin_client.delete_topics(topics=[name])
            return {name: "deleted"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            admin_client.close()

class TopicProvisioner:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.manager = TopicManager(bootstrap_servers=bootstrap_servers)

    def provision_topics(self) -> Dict[str, str]:
        return self.manager.provision_all_topics()
