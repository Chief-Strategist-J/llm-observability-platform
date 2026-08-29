#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

COMPOSE_FILE="$PACKAGE_DIR/deploy/docker/docker-compose.yaml"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f "$COMPOSE_FILE" ]; then
    echo -e "\033[0;34m[instrumentation-sdk] Cleaning up previous specific image...\033[0m"
    docker image rm docker-instrumentation-sdk instrumentation-sdk-instrumentation-sdk --force >/dev/null 2>&1 || true
    echo -e "\033[0;34m[instrumentation-sdk] Executing span capture inside Docker container (llmobs-network)...\033[0m"
    exec docker compose -f "$COMPOSE_FILE" run --rm instrumentation-sdk python examples/run_real_span_instrumentation.py "$@"
else
    export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:31414}"
    export OTEL_EXPORTER_ENDPOINT="${OTEL_EXPORTER_ENDPOINT:-http://localhost:31423}"
    export PYTHONPATH="src"
    
    PYTHON_EXE="python3"
    if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
        PYTHON_EXE="$PACKAGE_DIR/.venv/bin/python"
    elif [ -f "$PACKAGE_DIR/venv/bin/python" ]; then
        PYTHON_EXE="$PACKAGE_DIR/venv/bin/python"
    fi

    exec "$PYTHON_EXE" "$PACKAGE_DIR/examples/run_real_span_instrumentation.py" "$@"
fi
