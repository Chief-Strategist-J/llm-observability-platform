#!/bin/bash
set -e

USERNAME="chiefj"
IMAGE_NAME="instrumentation-sdk-api"
VERSION="v1.6.0"
DOCKERFILE="build/Dockerfile"

if [ -z "$DOCKER_PAT" ]; then
    echo "Error: DOCKER_PAT environment variable is not set."
    exit 1
fi

echo "$DOCKER_PAT" | docker login -u "$USERNAME" --password-stdin

docker build -f "$DOCKERFILE" -t "$USERNAME/$IMAGE_NAME:latest" .

docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:$VERSION"
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:1.6.0"
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:stable"
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:unstable"

docker push "$USERNAME/$IMAGE_NAME:latest"
docker push "$USERNAME/$IMAGE_NAME:$VERSION"
docker push "$USERNAME/$IMAGE_NAME:1.6.0"
docker push "$USERNAME/$IMAGE_NAME:stable"
docker push "$USERNAME/$IMAGE_NAME:unstable"
