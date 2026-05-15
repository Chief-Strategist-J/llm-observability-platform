#!/usr/bin/env bash
set -euo pipefail
PYTHON_EXE=python3
if [ -d ".venv" ]; then
    PYTHON_EXE="./.venv/bin/python3"
fi

PYTHONPATH=src $PYTHON_EXE -c "from api.index import health; print(health())"
