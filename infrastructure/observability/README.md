# Observability Infrastructure Module

This module provides a unified observability stack featuring Grafana, Prometheus, Loki, Jaeger, and OpenTelemetry.

> [!IMPORTANT]
> **Zero Localhost Policy**: This module is designed to work exclusively via Traefik-resolved URLs. Do not use `localhost` for testing, health checks, or API interaction.

## Prerequisites

Ensure the following tools are installed on your system:

- **Python 3.10+**: Required for the orchestration logic and service API.
- **Docker**: Engine for running containerized services.
- **Docker Compose**: Plugin for managing multi-container stacks.
- **Host Configuration**: One-time setup to enable Traefik URLs. Run:
  ```bash
  sudo ./infrastructure/observability/dependencies/configure_hosts.sh --apply
  ```

## Module Structure

- `api/`: REST API for service orchestration.
- `setup/`: Setup activities and configuration.
  - `activities/`: Orchestration logic.
- `dependencies/`: Requirements and install scripts.
- `hooks/`: Git hook installation and templates.

## Quick Start

1. **Install Dependencies**:
   ```bash
   ./infrastructure/observability/dependencies/install_deps.sh
   ```

2. **Start the Service**:
   This script handles port conflicts and dependency verification automatically:
   ```bash
   ./infrastructure/observability/start.sh
   ```

3. **Orchestrate via API (Traefik URLs Only)**:
   - Start Stack: `curl -X POST http://scaibu.observability-api/start`
   - Check Status: `curl http://scaibu.observability-api/status`
   - Stop Stack: `curl -X POST http://scaibu.observability-api/stop`

> [!IMPORTANT]
> **No Localhost**: Never use `localhost` for testing or health checks. All interactions must use Traefik hostnames.

## Development

Linting is configured via `.flake8`. Install git hooks for safety:
```bash
./infrastructure/observability/hooks/install_hooks.sh
```
