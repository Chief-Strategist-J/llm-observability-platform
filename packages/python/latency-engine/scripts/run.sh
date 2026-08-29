#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

COMPOSE_FILE="$PACKAGE_DIR/deploy/docker/docker-compose.yaml"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f "$COMPOSE_FILE" ]; then
    echo -e "\033[0;34m[latency-engine] Cleaning up previous specific image...\033[0m"
    docker image rm docker-latency-engine latency-engine-latency-engine --force >/dev/null 2>&1 || true
    echo -e "\033[0;34m[latency-engine] Starting Docker container (llmobs-network) with file-watcher auto-restart...\033[0m"
    exec docker compose -f "$COMPOSE_FILE" up --build
fi

export HEALTH_PORT="${HEALTH_PORT:-8003}"
export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9093}"
export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:31414}"
export REDIS_URL="${REDIS_URL:-redis://:llmobs_redis_s3cret_2024@localhost:31413/0}"
export CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
export CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-31421}"
export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-llmobs_clickhouse_s3cret_2026}"
export TEMPORAL_HOST="${TEMPORAL_HOST:-localhost:31424}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:31418}"
export SKIP_CONSOLE_EXPORTER="${SKIP_CONSOLE_EXPORTER:-true}"
export JWT_SECRET="${JWT_SECRET:-dev-secret-key-change-in-production}"
export PYTHONPATH="src"

if ! command -v nc >/dev/null 2>&1 || ! nc -z localhost 31418 >/dev/null 2>&1; then
    export SKIP_OTLP_EXPORTER="true"
else
    export SKIP_OTLP_EXPORTER="${SKIP_OTLP_EXPORTER:-false}"
fi

free_port() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        local pids
        pids=$(lsof -t -i:"${port}" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                if [ "$pid" != "$$" ]; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            done
        fi
    elif command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    fi
}

free_port "$HEALTH_PORT"
free_port "$PROMETHEUS_PORT"

PYTHON_EXE="python3"
if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/.venv/bin/python"
elif [ -f "$PACKAGE_DIR/venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/venv/bin/python"
fi

COMPOSE_FILE="$PACKAGE_DIR/deploy/docker/docker-compose.yaml"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f "$COMPOSE_FILE" ]; then
    echo -e "\033[0;34m[latency-engine] Cleaning up previous specific image...\033[0m"
    docker image rm docker-latency-engine latency-engine-latency-engine --force >/dev/null 2>&1 || true
    echo -e "\033[0;34m[latency-engine] Starting Docker container (llmobs-network) with file-watcher auto-restart...\033[0m"
    exec docker compose -f "$COMPOSE_FILE" up --build
fi

"$PACKAGE_DIR/scripts/migrate.sh" || true

exec "$PYTHON_EXE" "$PACKAGE_DIR/src/worker/index.py"
