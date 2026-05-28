#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src ./venv/bin/python3 scripts/migrate.py up
