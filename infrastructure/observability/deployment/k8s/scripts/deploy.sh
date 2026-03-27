#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
kubectl apply -f env/$ENV/pvc.yaml -n observability-$ENV
kubectl apply -f env/$ENV/resources.yaml -n observability-$ENV
kubectl apply -f env/$ENV/vpa.yaml -n observability-$ENV
kubectl apply -f env/$ENV/hpa.yaml -n observability-$ENV
kubectl set image deployment/observability-service observability-service=observability-service:$VERSION -n observability-$ENV
kubectl apply -f env/$ENV/deployment.yaml -n observability-$ENV
kubectl apply -f env/$ENV/ingress.yaml -n observability-$ENV
