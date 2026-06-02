#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="$(pwd)"
export SKIP_CONSOLE_EXPORTER=true

uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
