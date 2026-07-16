#!/bin/bash
set -e

# Color variables
GREEN='\033[0;32m'
BLUE='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_COMPOSE_FILE="$PKG_DIR/deploy/docker/docker-compose.yaml"
K8S_DIR="$PKG_DIR/deploy/kubernetes"
TF_AWS_DIR="$PKG_DIR/deploy/terraform/aws"
TF_GCP_DIR="$PKG_DIR/deploy/terraform/gcp"
TF_AZURE_DIR="$PKG_DIR/deploy/terraform/azure"
ANSIBLE_DIR="$PKG_DIR/deploy/ansible"

print_header() {
    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${GREEN}             LLM Observability Platform Deployment Tool            ${NC}"
    echo -e "${BLUE}===================================================================${NC}"
}

validate_prereqs() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    local missing=0

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[x] Docker is not installed.${NC}"
        missing=1
    else
        echo -e "${GREEN}[✓] Docker is installed.${NC}"
    fi

    if ! command -v kubectl &> /dev/null; then
        echo -e "${YELLOW}[!] kubectl is not installed (needed for Kubernetes).${NC}"
    else
        echo -e "${GREEN}[✓] kubectl is installed.${NC}"
    fi

    if ! command -v terraform &> /dev/null; then
        echo -e "${YELLOW}[!] Terraform is not installed (needed for Cloud).${NC}"
    else
        echo -e "${GREEN}[✓] Terraform is installed.${NC}"
    fi

    if ! command -v ansible-playbook &> /dev/null; then
        echo -e "${YELLOW}[!] Ansible (ansible-playbook) is not installed.${NC}"
    else
        echo -e "${GREEN}[✓] Ansible is installed.${NC}"
    fi

    if [ $missing -eq 1 ]; then
        echo -e "${RED}Please install missing critical prerequisites to continue.${NC}"
        return 1
    fi
    echo -e "${GREEN}All checks passed!${NC}"
}

deploy_docker() {
    echo -e "\n${YELLOW}Starting local Docker Compose stack...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    echo -e "${GREEN}Docker Compose stack started!${NC}"
    echo -e "${YELLOW}Setting up automated daily local backups (cron job)...${NC}"
    "$SCRIPT_DIR/setup-cron.sh"
    echo -e "${BLUE}You can access:${NC}"
    echo -e " - FastAPI Telemetry: http://localhost:8000"
    echo -e " - Grafana Observability Dashboards: http://localhost:3000 (admin/admin)"
    echo -e " - Prometheus UI: http://localhost:9090"
    echo -e " - Temporal Web UI: http://localhost:8080"
}

stop_docker() {
    echo -e "\n${YELLOW}Stopping local Docker Compose stack...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" down
    echo -e "${GREEN}Docker Compose stack stopped and resources cleaned up.${NC}"
}

deploy_k8s() {
    echo -e "\n${YELLOW}Deploying stack to Kubernetes...${NC}"
    echo -e "${BLUE}Step 1: Creating Namespace...${NC}"
    kubectl apply -f "$K8S_DIR/namespace.yaml"

    echo -e "${BLUE}Step 2: Enforcing Network Policies...${NC}"
    kubectl apply -f "$K8S_DIR/network-policies.yaml"

    echo -e "${BLUE}Step 3: Creating ConfigMaps and Secrets...${NC}"
    kubectl apply -f "$K8S_DIR/configmap.yaml"

    echo -e "${BLUE}Step 4: Provisioning Databases & Messaging Brokers...${NC}"
    kubectl apply -f "$K8S_DIR/databases.yaml"

    echo -e "${BLUE}Step 5: Provisioning Temporal Server...${NC}"
    kubectl apply -f "$K8S_DIR/temporal.yaml"

    echo -e "${BLUE}Step 6: Deploying Observability API...${NC}"
    kubectl apply -f "$K8S_DIR/api-deployment.yaml"

    echo -e "${BLUE}Step 7: Deploying Evaluation and Scorers Workers...${NC}"
    kubectl apply -f "$K8S_DIR/workers-deployment.yaml"

    echo -e "${BLUE}Step 8: Provisioning Automated Migrations Job...${NC}"
    kubectl apply -f "$K8S_DIR/migrations-job.yaml"

    echo -e "${BLUE}Step 9: Provisioning Automated Backup CronJob...${NC}"
    kubectl apply -f "$K8S_DIR/backup-cronjob.yaml"

    echo -e "${GREEN}Kubernetes resources deployed!${NC}"
    echo -e "${YELLOW}Run 'kubectl get pods -n llm-observability' to track startup status.${NC}"
}

deploy_aws() {
    echo -e "\n${YELLOW}Starting AWS Infrastructure Terraform run...${NC}"
    cd "$TF_AWS_DIR"
    terraform init
    terraform plan -out=tfplan
    echo -e "${YELLOW}Do you want to apply the plan? (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        terraform apply tfplan
        echo -e "${GREEN}AWS Infrastructure successfully created!${NC}"
    else
        echo -e "${YELLOW}Apply cancelled.${NC}"
    fi
}

deploy_gcp() {
    echo -e "\n${YELLOW}Starting GCP Infrastructure Terraform run...${NC}"
    cd "$TF_GCP_DIR"
    terraform init
    terraform plan -out=tfplan
    echo -e "${YELLOW}Do you want to apply the plan? (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        terraform apply tfplan
        echo -e "${GREEN}GCP Infrastructure successfully created!${NC}"
    else
        echo -e "${YELLOW}Apply cancelled.${NC}"
    fi
}

deploy_azure() {
    echo -e "\n${YELLOW}Starting Azure Infrastructure Terraform run...${NC}"
    cd "$TF_AZURE_DIR"
    terraform init
    terraform plan -out=tfplan
    echo -e "${YELLOW}Do you want to apply the plan? (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        terraform apply tfplan
        echo -e "${GREEN}Azure Infrastructure successfully created!${NC}"
    else
        echo -e "${YELLOW}Apply cancelled.${NC}"
    fi
}

deploy_ansible() {
    echo -e "\n${YELLOW}Starting Ansible network infrastructure deployment...${NC}"
    cd "$ANSIBLE_DIR"
    ansible-playbook -i hosts.ini playbook.yaml
    echo -e "${GREEN}Ansible playbook run finished!${NC}"
}

show_menu() {
    echo -e "\n${BLUE}Select deployment action:${NC}"
    echo -e " 1) Validate prerequisites"
    echo -e " 2) Start stack locally (Docker Compose)"
    echo -e " 3) Stop stack locally (Docker Compose)"
    echo -e " 4) Deploy stack to Kubernetes (kubectl)"
    echo -e " 5) Provision AWS cloud infrastructure (Terraform)"
    echo -e " 6) Provision GCP cloud infrastructure (Terraform)"
    echo -e " 7) Provision Azure cloud infrastructure (Terraform)"
    echo -e " 8) Provision VM nodes & deploy stack (Ansible)"
    echo -e " 9) Exit"
    echo -n "Option [1-9]: "
}

main() {
    print_header
    while true; do
        show_menu
        read -r opt
        case $opt in
            1) validate_prereqs ;;
            2) deploy_docker ;;
            3) stop_docker ;;
            4) deploy_k8s ;;
            5) deploy_aws ;;
            6) deploy_gcp ;;
            7) deploy_azure ;;
            8) deploy_ansible ;;
            9) echo -e "\n${GREEN}Goodbye!${NC}"; exit 0 ;;
            *) echo -e "\n${RED}Invalid option, try again.${NC}" ;;
        esac
    done
}

main
