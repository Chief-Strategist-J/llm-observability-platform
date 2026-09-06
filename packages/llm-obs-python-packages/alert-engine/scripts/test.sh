#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src
if [ -d ".venv" ]; then
  .venv/bin/pytest "$@"
else
  python3 -m pytest "$@"
fi
