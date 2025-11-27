#!/bin/bash
set -e

echo "Installing Python SDK in editable mode..."

cd "$(dirname "$0")/.."

pip install -e ".[dev]"

echo "SDK installed! Import with: from observability_sdk import init_observability"
