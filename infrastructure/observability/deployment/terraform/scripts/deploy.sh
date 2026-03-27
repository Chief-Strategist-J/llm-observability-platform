#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
cd env/$ENV
terraform init
terraform apply -auto-approve -var="app_version=$VERSION"
