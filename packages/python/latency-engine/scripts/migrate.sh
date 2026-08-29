#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:31414}"
export REDIS_URL="${REDIS_URL:-redis://:llmobs_redis_s3cret_2024@localhost:31413/0}"
export CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
export CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-31421}"
export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-llmobs_clickhouse_s3cret_2026}"
export PYTHONPATH="src"

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^llmobs-kafka-broker$"; then
    docker exec llmobs-kafka-broker /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic llm.spans.raw --partitions 3 --replication-factor 1 >/dev/null 2>&1 || true
    docker exec llmobs-kafka-broker /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic latency.anomalies.v1 --partitions 3 --replication-factor 1 >/dev/null 2>&1 || true
fi

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^llmobs-clickhouse-analytics$"; then
    docker exec llmobs-clickhouse-analytics clickhouse-client --password llmobs_clickhouse_s3cret_2026 --query "CREATE TABLE IF NOT EXISTS latency_checkpoints (model String, endpoint String, checkpoint_date Date, hour_of_day UInt8, p50_ttft_ms Float64, p95_ttft_ms Float64, p99_ttft_ms Float64, p50_total_ms Float64, p95_total_ms Float64, p99_total_ms Float64, sample_count UInt32, slo_violation_count UInt32, timestamp DateTime) ENGINE = MergeTree() ORDER BY (model, endpoint, checkpoint_date, hour_of_day);" >/dev/null 2>&1 || true
fi

PYTHON_EXE="python3"
if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/.venv/bin/python"
elif [ -f "$PACKAGE_DIR/venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/venv/bin/python"
fi

exec "$PYTHON_EXE" "$PACKAGE_DIR/src/infra/messaging/migrations/run_all_migrations.py"
