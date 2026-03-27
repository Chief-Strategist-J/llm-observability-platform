#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
helm upgrade --install observability-service . -f values/$ENV.yaml --set image.tag=$VERSION --wait --timeout 5m0s
