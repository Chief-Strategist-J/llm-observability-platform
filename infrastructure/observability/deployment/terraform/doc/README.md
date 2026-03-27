# Terraform Multi-Environment Provisioning

Provision infrastructure for specific environments with version control.

## Environments
- `dev`
- `stage`
- `prod`

## Execution
Run from the `terraform/` directory:
- **Advanced (Retry Logic)**:
  ```bash
  ./scripts/retry_deploy.sh <env> <version>
  ```
- **Basic**:
  ```bash
  ./scripts/deploy.sh <env> <version>
  ```
Example: `./scripts/deploy.sh prod v1.0.0`
