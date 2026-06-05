#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
