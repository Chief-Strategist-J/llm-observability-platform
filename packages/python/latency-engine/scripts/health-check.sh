#!/usr/bin/env bash
set -euo pipefail
HOST="${HEALTH_HOST:-localhost}"
PORT="${HEALTH_PORT:-8002}"
curl -sf "http://${HOST}:${PORT}/health" || exit 1
