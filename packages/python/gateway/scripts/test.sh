#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src:../python-shared pytest -q -o addopts="" src/features || true
