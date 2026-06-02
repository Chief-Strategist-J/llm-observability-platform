#!/usr/bin/env bash
set -euo pipefail

# Get directory where script resides
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../deploy/docker"

echo "Starting WebRTC Call Platform..."
docker compose up -d
echo "WebRTC Platform started."
