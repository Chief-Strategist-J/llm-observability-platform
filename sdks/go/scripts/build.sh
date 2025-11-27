#!/bin/bash
set -e

echo "Building Go SDK..."

cd "$(dirname "$0")/.."

go mod tidy
go test ./...
go vet ./...

echo "Build complete!"
