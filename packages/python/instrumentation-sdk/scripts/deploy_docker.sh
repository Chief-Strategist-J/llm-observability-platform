#!/bin/bash
# Deployment script for Instrumentation SDK API
# Usage: DOCKER_PAT=your_pat ./scripts/deploy_docker.sh

set -e

# Configuration
USERNAME="chiefj"
IMAGE_NAME="instrumentation-sdk-api"
TAG="latest"
DOCKERFILE="build/Dockerfile"

# Check for PAT
if [ -z "$DOCKER_PAT" ]; then
    echo "Error: DOCKER_PAT environment variable is not set."
    exit 1
fi

echo "Logging in to Docker Hub as $USERNAME..."
echo "$DOCKER_PAT" | docker login -u "$USERNAME" --password-stdin

echo "Building production image: $USERNAME/$IMAGE_NAME:$TAG..."
docker build -f "$DOCKERFILE" -t "$USERNAME/$IMAGE_NAME:$TAG" .

echo "Pushing image to Docker Hub..."
docker push "$USERNAME/$IMAGE_NAME:$TAG"

echo "=========================================="
echo "SUCCESS: Image deployed to $USERNAME/$IMAGE_NAME:$TAG"
echo "=========================================="
