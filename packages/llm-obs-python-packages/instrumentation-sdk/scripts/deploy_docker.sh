#!/bin/bash
set -e

USERNAME="chiefj"
IMAGE_NAME="instrumentation-sdk-api"
DOCKERFILE="build/Dockerfile"

if [ -z "$DOCKER_PAT" ]; then
    echo "Error: DOCKER_PAT environment variable is not set."
    exit 1
fi

VERSION=$(grep -oP 'version = "\K[^"]+' pyproject.toml)

echo "$DOCKER_PAT" | docker login -u "$USERNAME" --password-stdin

docker build -f "$DOCKERFILE" --build-arg WITH_KAFKA="true" -t "$USERNAME/$IMAGE_NAME:latest" .
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:$VERSION"
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:v$VERSION"
docker tag "$USERNAME/$IMAGE_NAME:latest" "$USERNAME/$IMAGE_NAME:stable"

docker build -f "$DOCKERFILE" --build-arg WITH_KAFKA="false" -t "$USERNAME/$IMAGE_NAME-nokafka:latest" .
docker tag "$USERNAME/$IMAGE_NAME-nokafka:latest" "$USERNAME/$IMAGE_NAME-nokafka:$VERSION"
docker tag "$USERNAME/$IMAGE_NAME-nokafka:latest" "$USERNAME/$IMAGE_NAME-nokafka:v$VERSION"
docker tag "$USERNAME/$IMAGE_NAME-nokafka:latest" "$USERNAME/$IMAGE_NAME-nokafka:stable"

docker push "$USERNAME/$IMAGE_NAME:latest"
docker push "$USERNAME/$IMAGE_NAME:$VERSION"
docker push "$USERNAME/$IMAGE_NAME:v$VERSION"
docker push "$USERNAME/$IMAGE_NAME:stable"

docker push "$USERNAME/$IMAGE_NAME-nokafka:latest"
docker push "$USERNAME/$IMAGE_NAME-nokafka:$VERSION"
docker push "$USERNAME/$IMAGE_NAME-nokafka:v$VERSION"
docker push "$USERNAME/$IMAGE_NAME-nokafka:stable"
