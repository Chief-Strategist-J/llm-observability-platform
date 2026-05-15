#!/usr/bin/env bash
set -euo pipefail
PYTHON_EXE=python3
if [ -d ".venv" ]; then
    PYTHON_EXE="./.venv/bin/python3"
fi

PYTHONPATH=src $PYTHON_EXE -c "from shared.contracts.validator import load_enrich_span_contract; load_enrich_span_contract(); print('contract ok')"
PYTHONPATH=src $PYTHON_EXE -m pytest -q
