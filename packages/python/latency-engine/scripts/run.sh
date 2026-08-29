#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

export HEALTH_PORT="${HEALTH_PORT:-8003}"
export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9093}"
export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:31414}"
export REDIS_URL="${REDIS_URL:-redis://:llmobs_redis_s3cret_2024@localhost:31413/0}"
export CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
export CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-31421}"
export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-llmobs_clickhouse_s3cret_2026}"
export TEMPORAL_HOST="${TEMPORAL_HOST:-localhost:31424}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:31418}"
export SKIP_OTLP_EXPORTER="${SKIP_OTLP_EXPORTER:-false}"
export SKIP_CONSOLE_EXPORTER="${SKIP_CONSOLE_EXPORTER:-true}"
export SKIP_JWT_VERIFICATION="${SKIP_JWT_VERIFICATION:-true}"
export PYTHONPATH="src"

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

"$PACKAGE_DIR/scripts/migrate.sh" || true

exec "$PYTHON_EXE" "$PACKAGE_DIR/src/worker/index.py"
