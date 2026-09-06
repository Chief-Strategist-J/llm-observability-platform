import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

sdk_root = Path(__file__).resolve().parents[3]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

from config.infra.env_config import service_config

@dataclass
class KafkaBrokerConfig:
    bootstrap_servers: List[str] = field(default_factory=lambda: [
        service_config.kafka_bootstrap_servers
    ])
    client_id: str = os.getenv("KAFKA_CLIENT_ID", "instrumentation-sdk-producer")
    acks: str = os.getenv("KAFKA_ACKS", "all")
    retries: int = int(os.getenv("KAFKA_RETRIES", "5"))
    max_in_flight_requests_per_connection: int = 1
    compression_type: str = os.getenv("KAFKA_COMPRESSION_TYPE", "gzip")
    batch_size: int = int(os.getenv("KAFKA_BATCH_SIZE", "32768"))
    linger_ms: int = int(os.getenv("KAFKA_LINGER_MS", "10"))
    security_protocol: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    sasl_mechanism: Optional[str] = os.getenv("KAFKA_SASL_MECHANISM", None)
    sasl_plain_username: Optional[str] = os.getenv("KAFKA_SASL_USERNAME", None)
    sasl_plain_password: Optional[str] = os.getenv("KAFKA_SASL_PASSWORD", None)

    @classmethod
    def from_env(cls) -> "KafkaBrokerConfig":
        raw_servers = service_config.kafka_bootstrap_servers
        servers = [s.strip() for s in raw_servers.split(",") if s.strip()]
        return cls(bootstrap_servers=servers)

kafka_broker_config = KafkaBrokerConfig.from_env()
