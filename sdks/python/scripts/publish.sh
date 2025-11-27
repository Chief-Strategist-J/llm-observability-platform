#!/bin/bash
set -e

echo "Publishing Python SDK..."

cd "$(dirname "$0")/.."

./scripts/build.sh

echo "Enter PyPI credentials or set TWINE_USERNAME and TWINE_PASSWORD"
python -m twine upload dist/*

echo "Published successfully!"
echo "Install with: pip install observability-sdk"
