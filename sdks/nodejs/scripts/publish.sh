#!/bin/bash
set -e

echo "Publishing Node.js SDK..."

cd "$(dirname "$0")/.."

./scripts/build.sh

echo "Publishing to npm registry..."
npm publish --access public

echo "Published successfully!"
echo "Install with: npm install @yourcompany/observability-sdk"
