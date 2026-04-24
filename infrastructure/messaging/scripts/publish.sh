#!/bin/bash
set -e

if [ -z "$PYPI_API_TOKEN" ]; then
    echo "Error: PYPI_API_TOKEN environment variable not set"
    exit 1
fi

echo "Publishing package to PyPI..."

# Build the package
./scripts/build.sh

# Upload to PyPI
python -m twine upload dist/* --username __token__ --password $PYPI_API_TOKEN

echo "Package published successfully!"
