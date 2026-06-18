#!/usr/bin/env bash
set -euo pipefail

PORT=${1:-8000}
curl -sf http://localhost:${PORT}/health
