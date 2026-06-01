#!/usr/bin/env bash
set -euo pipefail

IMAGE="chiefj/perplexity"
VERSION=$(python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['version'])")

echo "Building $IMAGE:$VERSION"
docker build -f build/Dockerfile -t "$IMAGE:latest" -t "$IMAGE:v$VERSION" -t "$IMAGE:stable" .

echo "Running smoke test"
docker run --rm \
  -e SKIP_CONSOLE_EXPORTER=true \
  -e SKIP_OTLP_EXPORTER=true \
  "$IMAGE:latest" \
  python -c "from api.rest.v1.app import create_app; create_app(); print('OK')"

echo "Pushing $IMAGE"
docker push "$IMAGE:latest"
docker push "$IMAGE:v$VERSION"
docker push "$IMAGE:stable"
