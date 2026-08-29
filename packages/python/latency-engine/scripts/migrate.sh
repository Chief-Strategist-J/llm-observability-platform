#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:31414}"
export REDIS_URL="${REDIS_URL:-redis://:llmobs_redis_s3cret_2024@localhost:31413/0}"
export CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
export CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-31421}"
export PYTHONPATH="src"

PYTHON_EXE="python3"
if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/.venv/bin/python"
elif [ -f "$PACKAGE_DIR/venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/venv/bin/python"
fi

exec "$PYTHON_EXE" "$PACKAGE_DIR/src/infra/messaging/migrations/run_all_migrations.py"
