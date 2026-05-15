#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -c "from shared.contracts.validator import load_enrich_span_contract; load_enrich_span_contract(); print('contract ok')"
PYTHONPATH=src pytest -q
