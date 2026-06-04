#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="chiefj/quality-baseline-worker"
VERSION="v1.0.0"

docker build -t $IMAGE_NAME:latest -f build/Dockerfile .
docker tag $IMAGE_NAME:latest $IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME:latest $IMAGE_NAME:stable

docker push $IMAGE_NAME:latest
docker push $IMAGE_NAME:$VERSION
docker push $IMAGE_NAME:stable

