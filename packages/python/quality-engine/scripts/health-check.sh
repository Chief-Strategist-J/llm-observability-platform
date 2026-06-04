#!/usr/bin/env bash
set -euo pipefail
# health-check.sh: exits 0 if health endpoint responds, 1 otherwise
HOST="${HEALTH_HOST:-localhost}"
PORT="${HEALTH_PORT:-8080}"
curl -sf "http://$HOST:$PORT/health" > /dev/null
