#!/bin/bash
set -e

echo "Building package..."

# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build the package
python -m build

echo "Build completed!"
ls -lh dist/
