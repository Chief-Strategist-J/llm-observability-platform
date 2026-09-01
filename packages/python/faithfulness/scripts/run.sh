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
    echo -e "\033[0;34m[faithfulness] Cleaning up previous image...\033[0m"
    docker image rm docker-faithfulness faithfulness-faithfulness --force >/dev/null 2>&1 || true
    echo -e "\033[0;34m[faithfulness] Starting Docker container...\033[0m"
    exec docker compose -f "$COMPOSE_FILE" up --build
fi

PYTHON_EXE="python3"
VENV_DIR=""

if [ -d "$PACKAGE_DIR/.venv" ]; then
    VENV_DIR="$PACKAGE_DIR/.venv"
elif [ -d "$PACKAGE_DIR/venv" ]; then
    VENV_DIR="$PACKAGE_DIR/venv"
fi

if [ -n "$VENV_DIR" ]; then
    PYTHON_EXE="$VENV_DIR/bin/python"
else
    echo -e "\033[1;33m[faithfulness] Virtual environment missing. Creating .venv...\033[0m"
    python3 -m venv "$PACKAGE_DIR/.venv" || true
    if [ -f "$PACKAGE_DIR/.venv/bin/python" ]; then
        VENV_DIR="$PACKAGE_DIR/.venv"
        PYTHON_EXE="$VENV_DIR/bin/python"
    fi
fi

if [ -f "$PACKAGE_DIR/pyproject.toml" ] || [ -f "$PACKAGE_DIR/requirements.txt" ]; then
    if ! "$PYTHON_EXE" -c "import uvicorn, fastapi" 2>/dev/null; then
        echo -e "\033[1;33m[faithfulness] Dependencies missing. Auto-installing packages...\033[0m"
        "$PYTHON_EXE" -m pip install --upgrade pip >/dev/null 2>&1 || true
        if [ -f "$PACKAGE_DIR/pyproject.toml" ]; then
            "$PYTHON_EXE" -m pip install -e "$PACKAGE_DIR" || "$PYTHON_EXE" -m pip install uvicorn fastapi
        elif [ -f "$PACKAGE_DIR/requirements.txt" ]; then
            "$PYTHON_EXE" -m pip install -r "$PACKAGE_DIR/requirements.txt"
        fi
    fi
fi

export HEALTH_PORT="${HEALTH_PORT:-8006}"
export PYTHONPATH="$PACKAGE_DIR/src"

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

if [ -f "$PACKAGE_DIR/scripts/migrate.sh" ]; then
    echo -e "\033[0;34m[faithfulness] Executing database migrations...\033[0m"
    "$PACKAGE_DIR/scripts/migrate.sh" || true
fi

echo -e "\033[0;32m[faithfulness] Starting service on port ${HEALTH_PORT}...\033[0m"
exec $PYTHON_EXE -m uvicorn api.rest.v1.app:app --host 0.0.0.0 --port "$HEALTH_PORT"
