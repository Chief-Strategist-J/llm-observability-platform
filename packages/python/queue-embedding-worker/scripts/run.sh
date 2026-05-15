#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -c "from api.index import health; print(health())"
