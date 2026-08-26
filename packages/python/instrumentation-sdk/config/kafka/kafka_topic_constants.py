from dataclasses import dataclass, field

@dataclass(frozen=True)
class KafkaTopicConstants:
    DEFAULT_PARTITIONS: int = 3
    DEFAULT_REPLICATION_FACTOR: int = 1
    DEFAULT_RETENTION_MS: int = 604800000
    DEFAULT_CLEANUP_POLICY: str = "delete"
    DEFAULT_MIN_INSYNC_REPLICAS: int = 1
    CLIENT_ID: str = "instrumentation-sdk-topic-provisioner"

topic_constants = KafkaTopicConstants()
