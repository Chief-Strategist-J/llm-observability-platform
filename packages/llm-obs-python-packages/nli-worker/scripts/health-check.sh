#!/usr/bin/env bash
set -euo pipefail

# Health check for nli-worker by hitting the local /healthz endpoint
PORT=${1:-8009}

if command -v curl >/dev/null 2>&1; then
    curl -sf "http://localhost:${PORT}/healthz" >/dev/null
else
    python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/healthz')"
fi
