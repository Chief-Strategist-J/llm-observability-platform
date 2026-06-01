#!/usr/bin/env bash
set -euo pipefail
SKIP_CONSOLE_EXPORTER=true SKIP_OTLP_EXPORTER=true \
  pytest tests/ --cov=src --cov-report=term-missing -v
