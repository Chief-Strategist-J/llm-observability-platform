#!/usr/bin/env bash
set -euo pipefail

VERSION=$(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d['project']['version'])
")

IMAGE="chiefj/event-cost-worker"

echo "Building event-cost-worker v${VERSION}"
docker build -f build/Dockerfile -t "${IMAGE}:latest" .
docker tag "${IMAGE}:latest" "${IMAGE}:v${VERSION}"
docker tag "${IMAGE}:latest" "${IMAGE}:stable"

echo "Running tests inside container"
docker run --rm "${IMAGE}:latest" python -m pytest src/handlers/llm_spans_raw/tests/unit -q

echo "Pushing tags: latest, v${VERSION}, stable"
docker push "${IMAGE}:latest"
docker push "${IMAGE}:v${VERSION}"
docker push "${IMAGE}:stable"

echo "Done: ${IMAGE}:v${VERSION}"
