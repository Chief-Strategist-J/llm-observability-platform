#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./build.sh <dev|stage|prod> <version>"
    exit 1
fi
IMAGE_NAME="observability-service"
TAG="$VERSION-$ENV"
REGISTRY="your-registry-url"
docker build -t $IMAGE_NAME:$TAG -f deployment/docker/Dockerfile .
docker tag $IMAGE_NAME:$TAG $REGISTRY/$IMAGE_NAME:$TAG
docker push $REGISTRY/$IMAGE_NAME:$TAG
