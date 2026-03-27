# Ansible Multi-Environment Setup

Provision environment-level dependencies for specific environments.

## Environments
- `dev`
- `stage`
- `prod`

## Execution
Run from the `ansible/` directory:
```bash
./scripts/deploy.sh <env> <version>
```
Example: `./scripts/deploy.sh prod v1.0.0`
