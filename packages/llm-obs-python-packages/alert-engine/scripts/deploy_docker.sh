#!/usr/bin/env bash
# deploy_docker.sh — Build, validate, and push Docker image with proper tags (latest, version, stable)
set -euo pipefail

IMAGE="chiefj/alert-engine"
VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)

echo "=== Building Docker Image: ${IMAGE} ==="
docker build -f build/Dockerfile -t "${IMAGE}:latest" -t "${IMAGE}:v${VERSION}" -t "${IMAGE}:stable" .

echo "=== Running Container Validation Tests ==="
docker run --rm \
  -v "$(pwd)/tests:/app/tests" \
  -e PYTHONPATH=/app/src \
  "${IMAGE}:latest" pytest /app/tests -v --tb=short

echo "=== Pushing Docker Image Tags ==="
docker push "${IMAGE}:latest"
docker push "${IMAGE}:v${VERSION}"
docker push "${IMAGE}:stable"

echo "=== Deleting Local Docker Images ==="
docker rmi "${IMAGE}:latest" "${IMAGE}:v${VERSION}" "${IMAGE}:stable"

echo "=== Docker deploy completed successfully! ==="
