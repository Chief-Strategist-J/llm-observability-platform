#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./retry_deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
MAX_RETRIES=3
RETRY_COUNT=0
deploy_status=1
while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ $deploy_status -ne 0 ]; do
    ./scripts/deploy.sh $ENV $VERSION
    deploy_status=$?
    if [ $deploy_status -ne 0 ]; then
        RETRY_COUNT=$((RETRY_COUNT+1))
        sleep 15
    fi
done
exit $deploy_status
