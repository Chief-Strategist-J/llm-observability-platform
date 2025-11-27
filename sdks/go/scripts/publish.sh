#!/bin/bash
set -e

echo "Publishing Go SDK..."

cd "$(dirname "$0")/.."

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./publish.sh v1.0.0"
    exit 1
fi

./scripts/build.sh

git tag $VERSION
git push origin $VERSION

echo "Published $VERSION successfully!"
echo "Install with: go get github.com/yourcompany/observability-sdk-go@$VERSION"
