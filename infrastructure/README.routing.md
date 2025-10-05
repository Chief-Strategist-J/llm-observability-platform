# Routing Services

Shared Traefik proxy and routing configuration for all services.

## Quick Start

```bash
# Start routing services only
docker-compose -f infrastructure/docker-compose.routing.yml --profile routing up -d

# Start with all services
docker-compose -f infrastructure/docker-compose.routing.yml --profile routing \
  -f infrastructure/databases/docker-compose.databases.yml --profile databases \
  -f service/kg-service/docker-compose.yml up -d
```

## Services

- **Traefik**: Reverse proxy with automatic SSL certificates via Let's Encrypt

## Features

- **Automatic SSL**: Free certificates for HTTPS
- **Service Discovery**: Automatically routes to labeled services
- **Load Balancing**: Distributes traffic across service instances
- **Health Checks**: Routes only to healthy services

## Access Points

- **Traefik Dashboard**: http://localhost:8080
- **Services**: Configured via labels on service containers

## Environment Variables

- `ROUTING_SUBNET`: Routing network subnet (default: 172.28.0.0/16)

## Usage with Services

Services connect to the routing network and use Traefik labels:

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.myapp.rule=Host(`myapp.localhost`)
  - traefik.http.routers.myapp.entrypoints=web
  - traefik.http.services.myapp.loadbalancer.server.port=8000
```

See CHANGELOG.md for detailed changes.
