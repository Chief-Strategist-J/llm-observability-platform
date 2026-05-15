# Changelog - Queue Embedding Worker

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-05-15

### Added
- **REST API Layer**: Implemented a FastAPI-based management layer with `/health` and `/execute` endpoints for remote orchestration and testing.
- **Dockerization**: Added specialized Dockerfiles (`Prod`, `Dev`, `Test`) with optimized layer caching.
- **Deployment**: Integrated `scripts/deploy_docker.sh` for automated registry updates to Docker Hub.
- **Observability**: Standardized OTEL tracing across the worker execution flow.

### Changed
- **Build System**: Migrated to a feature-isolated build structure to support efficient caching of dependencies.

### Security
- Isolated test environments using dedicated `Dockerfile.test`.
