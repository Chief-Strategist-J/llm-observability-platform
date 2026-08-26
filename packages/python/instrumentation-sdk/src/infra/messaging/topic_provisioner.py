from typing import Dict, Any, List, Optional
from kafka.admin import KafkaAdminClient, NewTopic
from src.infra.messaging.broker_config import kafka_broker_config

class TopicProvisioner:
    def __init__(self, bootstrap_servers: Optional[List[str]] = None) -> None:
        self.bootstrap_servers = bootstrap_servers or kafka_broker_config.bootstrap_servers

    def provision_topics(self, topic_specs: List[Dict[str, Any]]) -> Dict[str, str]:
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id="instrumentation-sdk-topic-provisioner"
        )
        results = {}
        new_topics = []

        try:
            existing_topics = set(admin_client.list_topics())
            for spec in topic_specs:
                name = spec["name"]
                if name in existing_topics:
                    results[name] = "exists"
                    continue

                new_topics.append(NewTopic(
                    name=name,
                    num_partitions=spec.get("num_partitions", 3),
                    replication_factor=spec.get("replication_factor", 1),
                    topic_configs=spec.get("configs", {})
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
