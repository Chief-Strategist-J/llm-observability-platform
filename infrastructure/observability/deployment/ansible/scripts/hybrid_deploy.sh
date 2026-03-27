#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./hybrid_deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
echo "Step 1: Provisioning Infrastructure with Terraform"
cd ../terraform && ./scripts/deploy.sh $ENV $VERSION && cd ../ansible
echo "Step 2: Extracting Terraform Outputs"
TF_OUTPUTS=$(cd ../terraform/env/$ENV && terraform output -json)
CLUSTER_ENDPOINT=$(echo $TF_OUTPUTS | jq -r '.eks_cluster_endpoint.value')
ECR_URL=$(echo $TF_OUTPUTS | jq -r '.ecr_repository_url.value')
echo "Step 3: Configuring OS Layer"
ansible-playbook -i inventory/$ENV.ini playbooks/setup_env.yml \
    -e "cluster_endpoint=$CLUSTER_ENDPOINT" \
    -e "ecr_url=$ECR_URL" \
    -e "app_version=$VERSION" \
    -e "env=$ENV"
echo "Step 4: Orchestrating Container Ecosystem (K8s/Helm)"
ansible-playbook playbooks/orchestrate_k8s.yml \
    -e "app_version=$VERSION" \
    -e "env=$ENV"
echo "Step 5: Complex Traffic Orchestration"
ansible-playbook -i inventory/$ENV.ini playbooks/deploy_app.yml \
    -e "app_version=$VERSION" \
    -e "env=$ENV"
