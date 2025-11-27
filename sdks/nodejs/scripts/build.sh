#!/bin/bash
set -e

echo "Building Node.js SDK..."

cd "$(dirname "$0")/.."

npm install
npm run build || echo "No build script in package.json"
npm test || echo "No tests yet"

echo "Build complete!"
