#!/bin/bash
set -e

echo "Linking Node.js SDK for local development..."

cd "$(dirname "$0")/.."

npm link

echo "SDK linked!"
echo "In your microservice run: npm link @yourcompany/observability-sdk"
