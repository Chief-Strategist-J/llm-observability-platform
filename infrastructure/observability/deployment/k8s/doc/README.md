# Kubernetes Multi-Environment Deployment

Deploy the observability service to specific environments with version control.

## Environments
- `dev`
- `stage`
- `prod`

## Execution
Run from the `k8s/` directory:
- **Advanced (Retry Logic)**:
  ```bash
  ./scripts/retry_deploy.sh <env> <version>
  ```
- **Basic**:
  ```bash
  ./scripts/deploy.sh <env> <version>
  ```
Example: `./scripts/deploy.sh prod v1.0.0`
