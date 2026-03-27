# Observability Infrastructure

This module provides a production-ready, highly organized, and durable observability stack. It handles environment provisioning, container orchestration, and large-scale Kubernetes deployments with automated scaling and persistence.

## Infrastructure Suite

### Environment & Network Setup
- **Ansible**: Found in `deployment/ansible/`. Provisions the OS (Ubuntu/Linux) and installs core dependencies (Docker, Python, Temporal).
- **Master Setup**: Found in `setup/scripts/setup_all.sh`. A unified orchestrator for the entire stack.

### Deployment Platforms
Every component below follows a standardized interface with `scripts/deploy.sh` and `scripts/retry_deploy.sh`.

- **Docker Compose**: Located in `deployment/docker/`. Local orchestration with named volumes.
- **Helm**: Located in `deployment/helm/`. Kubernetes charts with persistence and scaling.
- **Kubernetes**: Located in `deployment/k8s/`. Advanced manifests including HPA, VPA, and Ingress.
- **Terraform**: Located in `deployment/terraform/`. Versioned cloud infrastructure provisioning.

## CI/CD & Hooks
Comprehensive CI/CD integration and automated hooks are located in the `ci-cd/` directory.

## No-Comment Policy
To ensure clean automation and processing, all configuration, manifest, and script files are strictly comment-free.
