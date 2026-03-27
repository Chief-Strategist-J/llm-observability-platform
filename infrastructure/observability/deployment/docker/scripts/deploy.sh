#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
export ENV=$ENV
export VERSION=$VERSION
docker-compose -f docker/docker-compose.yml up -d
