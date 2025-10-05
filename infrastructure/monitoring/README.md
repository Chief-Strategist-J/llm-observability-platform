# Monitoring Services

Unified monitoring stack with Loki, Promtail, and Grafana for centralized logging and observability.

## Quick Start

```bash
# Start monitoring stack only
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml --profile monitoring up -d

# Start with all services
docker-compose -f infrastructure/monitoring/docker-compose.monitoring.yml --profile monitoring -f infrastructure/databases/docker-compose.databases.yml --profile databases -f service/kg-service/docker-compose.yml up -d
```

## Services

- **Loki**: Log aggregation and querying
- **Promtail**: Log collection agent (collects from all Docker containers)
- **Grafana**: Visualization and dashboards

## Access Points

- **Grafana**: http://localhost:3000 (admin/admin)
- **Loki**: http://localhost:3100 (for log queries)

## Environment Variables

- `MONITORING_SUBNET`: Network subnet (default: 172.27.0.0/16)

## Features

- **Centralized Logging**: All service logs in one place
- **Container Discovery**: Automatically discovers and labels logs by service
- **Dashboards**: Pre-configured dashboards for service monitoring
- **Conditional Activation**: Only runs when explicitly requested

See CHANGELOG.md for detailed changes.
