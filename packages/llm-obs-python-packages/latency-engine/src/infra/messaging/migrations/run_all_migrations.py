from __future__ import annotations
import logging
import socket
import clickhouse_connect
from config import load_config
from infra.messaging.migrations.kafka_topic_migration import KafkaTopicMigration

logger = logging.getLogger(__name__)

CREATE_LATENCY_CHECKPOINTS_DDL = """
CREATE TABLE IF NOT EXISTS default.latency_checkpoints (
    model String,
    endpoint String,
    checkpoint_date Date,
    hour_of_day UInt8,
    p50_ttft_ms Float64,
    p95_ttft_ms Float64,
    p99_ttft_ms Float64,
    p50_total_ms Float64,
    p95_total_ms Float64,
    p99_total_ms Float64,
    sample_count UInt32,
    slo_violation_count UInt32,
    timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (model, endpoint, checkpoint_date, hour_of_day)
"""

def is_broker_alias_resolvable(bootstrap_servers: str) -> bool:
    try:
        parts = bootstrap_servers.split(",")[0].strip().split(":")
        host = parts[0]
        socket.gethostbyname(host)
        return True
    except Exception:
        return False

def run_all_migrations() -> None:
    cfg = load_config()

    if is_broker_alias_resolvable(cfg.kafka_bootstrap_servers):
        try:
            topic_migration = KafkaTopicMigration()
            topic_migration.run_migrations()
        except Exception as exc:
            logger.warning("Kafka topic migrations skipped: %s", exc)
    else:
        logger.info("Kafka broker host alias unresolvable — topic migration handled via container exec.")

    try:
        client = clickhouse_connect.get_client(
            host=cfg.clickhouse_host,
            port=cfg.clickhouse_port,
            username=cfg.clickhouse_username,
            password=cfg.clickhouse_password,
        )
        client.command("CREATE DATABASE IF NOT EXISTS default")
        client.command(CREATE_LATENCY_CHECKPOINTS_DDL)
        logger.info("ClickHouse table latency_checkpoints migration verified.")
    except Exception as exc:
        logger.warning("ClickHouse table migration skipped: %s", exc)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_migrations()
