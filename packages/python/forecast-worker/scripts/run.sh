#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PACKAGE_DIR"

COMPOSE_FILE="$PACKAGE_DIR/deploy/docker/docker-compose.yaml"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="$PACKAGE_DIR/deploy/docker-compose.yaml"
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f "$COMPOSE_FILE" ]; then
    echo -e "\033[0;34m[forecast-worker] Cleaning up previous image...\033[0m"
    docker image rm docker-forecast-worker forecast-worker-forecast-worker --force >/dev/null 2>&1 || true
    echo -e "\033[0;34m[forecast-worker] Starting Docker container...\033[0m"
    exec docker compose -f "$COMPOSE_FILE" up --build
fi

export HEALTH_PORT="${HEALTH_PORT:-8017}"
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

PYTHON_EXE="python3"
if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/.venv/bin/python"
elif [ -f "$PACKAGE_DIR/venv/bin/python" ]; then
    PYTHON_EXE="$PACKAGE_DIR/venv/bin/python"
fi

if [ -f "$PACKAGE_DIR/scripts/migrate.sh" ]; then
    echo -e "\033[0;34m[forecast-worker] Executing database migrations...\033[0m"
    "$PACKAGE_DIR/scripts/migrate.sh" || true
fi

echo -e "\033[0;32m[forecast-worker] Starting service on port ${HEALTH_PORT}...\033[0m"
exec $PYTHON_EXE src/worker/index.py
