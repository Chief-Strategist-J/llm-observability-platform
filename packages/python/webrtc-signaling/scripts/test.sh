#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="$(pwd)"
export SKIP_CONSOLE_EXPORTER=true

pytest tests/unit/ --cov=src --cov-report=term-missing --tb=short -q
