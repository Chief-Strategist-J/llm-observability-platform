from __future__ import annotations
import os
from dataclasses import dataclass, field

@dataclass
class KafkaBrokerConfig:
    bootstrap_servers: str = "localhost:31414"
    client_id: str = "latency-engine"
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    request_timeout_ms: int = 30000
    retry_backoff_ms: int = 500
    max_retries: int = 5
    extra_config: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> KafkaBrokerConfig:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:31414")
        client_id = os.getenv("KAFKA_CLIENT_ID", "latency-engine")
        sec_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        sasl_mech = os.getenv("KAFKA_SASL_MECHANISM")
        sasl_user = os.getenv("KAFKA_SASL_USERNAME")
        sasl_pass = os.getenv("KAFKA_SASL_PASSWORD")

        return cls(
            bootstrap_servers=bootstrap,
            client_id=client_id,
            security_protocol=sec_protocol,
            sasl_mechanism=sasl_mech,
            sasl_username=sasl_user,
            sasl_password=sasl_pass,
        )

    def to_confluent_config(self) -> dict[str, str | int]:
        config: dict[str, str | int] = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": self.client_id,
            "security.protocol": self.security_protocol,
        }
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            config["sasl.username"] = self.sasl_username
        if self.sasl_password:
            config["sasl.password"] = self.sasl_password
        for k, v in self.extra_config.items():
            config[k] = v
        return config
