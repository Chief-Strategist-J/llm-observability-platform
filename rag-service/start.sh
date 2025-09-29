#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous containers
docker compose down -v 2>/dev/null || true

echo "Cleaning old image (if any)..."
docker rmi rag-service-api 2>/dev/null || true

echo "Starting Qdrant..."
docker compose up -d qdrant

echo "Waiting for Qdrant (max 60s)..."
for i in {1..30}; do
  if curl -sf http://localhost:6333 >/dev/null 2>&1; then
    echo "Qdrant ready"
    break
  fi
  sleep 2
  if [ $i -eq 30 ]; then
    echo "Qdrant failed to start"; exit 1
  fi
done

echo "Building API..."
docker compose build --no-cache api

echo "Starting API..."
docker compose up -d api

echo "Waiting for API health (max 30s)..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "API ready at http://localhost:8000/docs"
    exit 0
  fi
  sleep 1
done
echo "API failed to pass health check. Run ./debug.sh"
exit 1
