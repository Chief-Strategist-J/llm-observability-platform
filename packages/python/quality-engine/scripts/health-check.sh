#!/usr/bin/env bash
# health-check.sh — Event worker health check (tracing-rules-for-workers.md line 17)
# Verifies: (1) HTTP health endpoint responds, (2) Kafka broker is reachable
# Exit 0 = healthy, 1 = unhealthy. Timeout: 5s max per check.
set -euo pipefail

HEALTH_HOST="${HEALTH_HOST:-localhost}"
HEALTH_PORT="${HEALTH_PORT:-8080}"
KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"

# Split host:port
KAFKA_HOST="${KAFKA_BOOTSTRAP%%:*}"
KAFKA_PORT="${KAFKA_BOOTSTRAP##*:}"

# 1. Verify HTTP health endpoint
curl -sf --max-time 5 "http://$HEALTH_HOST:$HEALTH_PORT/health" > /dev/null || {
    echo "UNHEALTHY: /health endpoint unreachable"
    exit 1
}

# 2. Verify Kafka broker TCP connectivity (consumer group registration proxy check)
timeout 5 bash -c "echo > /dev/tcp/$KAFKA_HOST/$KAFKA_PORT" 2>/dev/null || {
    echo "UNHEALTHY: Kafka broker $KAFKA_BOOTSTRAP unreachable"
    exit 1
}

echo "HEALTHY"
exit 0
