#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHONPATH=src uvicorn api.rest.v1.app:app --host 0.0.0.0 --port 8009
