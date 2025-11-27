#!/bin/bash
set -e

echo "Building Python SDK..."

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install build twine

python -m build

echo "Build complete! Packages in dist/"
ls -lh dist/
