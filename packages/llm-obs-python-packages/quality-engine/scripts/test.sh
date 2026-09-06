#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$PACKAGE_DIR/src"

echo "[quality-engine] Running tests..."
pytest "$PACKAGE_DIR/tests" --cov=src --cov-report=term-missing -v
