#!/usr/bin/env bash
set -euo pipefail

IMAGE="chiefj/faithfulness"
VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)

docker build -f build/Dockerfile -t "${IMAGE}:latest" -t "${IMAGE}:v${VERSION}" -t "${IMAGE}:stable" .
docker run --rm -v "$(pwd)/tests:/app/tests" "${IMAGE}:latest" pytest tests/ -v --tb=short
docker push "${IMAGE}:latest"
docker push "${IMAGE}:v${VERSION}"
docker push "${IMAGE}:stable"
