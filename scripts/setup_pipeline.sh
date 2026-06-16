#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "🚀 LLM Observability & Quality Pipeline Setup"
echo "=========================================="

# 1. Network configuration check
echo "⚙️  Verifying Docker Network..."
NETWORK_NAME="docker_default"
if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "⚠️  Docker network '$NETWORK_NAME' not found, creating..."
    docker network create "$NETWORK_NAME"
else
    echo "✅ Docker network '$NETWORK_NAME' is present."
fi

# 2. Database migrations check
echo "⚙️  Verifying Database Schema..."
SQL_SCHEMA="
CREATE TABLE IF NOT EXISTS quality_scores (
    span_id VARCHAR(255) PRIMARY KEY,
    trace_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    latency_ms_total DOUBLE PRECISION NOT NULL,
    finish_reason VARCHAR(255) NOT NULL,
    cost_usd_micro INTEGER NOT NULL,
    price_version VARCHAR(255) NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    prompt_text TEXT,
    response_text TEXT,
    review_status VARCHAR(50) DEFAULT 'pending',
    reviewed_at TIMESTAMPTZ
);
"

if docker ps | grep -q "quality-engine-postgres"; then
    echo "📦 Initializing quality_scores table in PostgreSQL..."
    docker exec -i quality-engine-postgres psql -U postgres -d quality_engine_db -c "$SQL_SCHEMA"
    echo "✅ Database schema updated successfully."
else
    echo "❌ PostgreSQL container (quality-engine-postgres) is not running!"
    exit 1
fi

# 3. Kafka topics creation
echo "⚙️  Verifying Kafka topics..."
if docker ps | grep -q "docker-kafka-1"; then
    for TOPIC in "llm.spans.sampled" "llm.quality.scores" "llm.spans.raw"; do
        if docker exec docker-kafka-1 kafka-topics --list --bootstrap-server localhost:9094 2>/dev/null | grep -q "^$TOPIC$"; then
            echo "✅ Kafka topic '$TOPIC' already exists."
        else
            echo "⚡ Creating Kafka topic '$TOPIC'..."
            docker exec docker-kafka-1 kafka-topics --create --topic "$TOPIC" --bootstrap-server localhost:9094 --partitions 1 --replication-factor 1
        fi
    done
else
    echo "❌ Kafka container (docker-kafka-1) is not running!"
    exit 1
fi

# 4. Restart/Reconnect Observability and Quality Engine on the proper network
echo "⚙️  Reconnecting Observability stack and Quality Engine to network..."
docker stop quality-observability-stack >/dev/null 2>&1 || true
docker rm quality-observability-stack >/dev/null 2>&1 || true

echo "⚡ Starting quality-observability-stack container on '$NETWORK_NAME'..."
docker run -d --name quality-observability-stack \
  -p 4317:4317 -p 9090:9090 -p 3002:3000 -p 8002:8000 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 \
  --network="$NETWORK_NAME" \
  chiefj/instrumentation-sdk-api:latest

# Copy dashboard JSONs to ensure quality-engine and other updated dashboards are provisioned
docker cp packages/python/instrumentation-sdk/build/dashboards/. quality-observability-stack:/etc/grafana/provisioning/dashboards/json/

echo "⚡ Restarting quality-engine worker to re-subscribe cleanly..."
docker restart quality-engine

echo "=========================================="
echo "🎉 Pipeline setup validation complete!"
echo "=========================================="
