#!/bin/bash

# Deployment script for queue-embedding-worker
# Usage: ./scripts/deploy_docker.sh

set -e

IMAGE_NAME="chiefj/queue-embedding-worker"
VERSION="v1.1.0"

echo "=========================================="
echo "Starting deployment for $IMAGE_NAME"
echo "=========================================="

# Build the production image from the local context
echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest -f build/Dockerfile .

# Tagging
echo "Tagging image..."
docker tag $IMAGE_NAME:latest $IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME:latest $IMAGE_NAME:stable

# Pushing
echo "Pushing to Docker Hub..."
docker push $IMAGE_NAME:latest
docker push $IMAGE_NAME:$VERSION
docker push $IMAGE_NAME:stable

echo "=========================================="
echo "SUCCESS: Image deployed to $IMAGE_NAME"
echo "=========================================="
