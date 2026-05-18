#!/bin/bash
set -e

IMAGE_NAME="chiefj/ai-service"
VERSION="v1.0.0"

docker build -t $IMAGE_NAME:latest .

docker tag $IMAGE_NAME:latest $IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME:latest $IMAGE_NAME:stable

if [ -n "$DOCKER_PASSWORD" ]; then
    echo "$DOCKER_PASSWORD" | docker login -u chiefj --password-stdin
    docker push $IMAGE_NAME:latest
    docker push $IMAGE_NAME:$VERSION
    docker push $IMAGE_NAME:stable
else
    echo "DOCKER_PASSWORD not set. Skipping registry push."
fi
