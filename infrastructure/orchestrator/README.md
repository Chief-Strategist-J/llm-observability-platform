# Centralized Configuration Guide

## Overview

This guide explains how to use the centralized environment configuration for deploying all infrastructure services with proper port management, security, and network isolation.

## Quick Start

### 1. Setup Environment File

```bash
# Copy the template to create your .env file
cp infrastructure/orchestrator/.env.template infrastructure/orchestrator/.env

# Edit the .env file with your specific configuration
nano infrastructure/orchestrator/.env
```

**Important**: Update these values before deployment:
- `TRAEFIK_BASIC_AUTH`: Generate with `htpasswd -nb admin your_password`
- `API_KEY`: Generate a secure random string
- All passwords (MongoDB, Neo4j, Grafana, etc.)
- `ACME_EMAIL`: Your email for Let's Encrypt certificates

### 2. Create Networks

```bash
# Create all required Docker networks
cd infrastructure/orchestrator
bash scripts/create-networks.sh
```

This creates 4 isolated networks:
- `observability-network` (172.20.0.0/16)
- `data-network` (172.21.0.0/16)
- `messaging-network` (172.22.0.0/16)
- `cicd-network` (172.23.0.0/16)

### 3. Deploy Services

Start services individually or use docker-compose:

```bash
# Deploy Traefik first (reverse proxy)
cd infrastructure/orchestrator/config/docker
docker-compose -f traefik-dynamic-docker.yaml --env-file ../../.env up -d

# Deploy observability stack
docker-compose -f prometheus-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f grafana-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f loki-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f tempo-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f jaeger-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f otel-collector-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f promtail-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f alertmanager-docker.yaml --env-file ../../.env up -d

# Deploy databases
docker-compose -f mongodb-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f redis-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f neo4j-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f qdrant-dynamic-docker.yaml --env-file ../../.env up -d

# Deploy messaging
docker-compose -f kafka-dynamic-docker.yaml --env-file ../../.env up -d

# Deploy admin UIs
docker-compose -f mongoexpress-dynamic-docker.yaml --env-file ../../.env up -d

# Deploy CI/CD
docker-compose -f argocd-server-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f argocd-repo-dynamic-docker.yaml --env-file ../../.env up -d
```

### 4. Access Services

All external services are accessible via HTTPS through Traefik at:

| Service | URL | Authentication |
|---------|-----|----------------|
| **Traefik Dashboard** | https://traefik-0.localhost | Basic Auth (admin/password) |
| **Grafana** | https://grafana-0.localhost | Grafana Login |
| **Prometheus** | https://prometheus-0.localhost | Basic Auth |
| **Loki** | https://loki-0.localhost | Basic Auth |
| **Tempo** | https://tempo-0.localhost | Basic Auth |
| **Jaeger** | https://jaeger-0.localhost | None |
| **Mongo Express** | https://mongoexpress-0.localhost | Basic Auth |
| **Neo4j Browser** | https://neo4j-0.localhost | Neo4j Login |
| **Qdrant UI** | https://qdrant-0.localhost | None |
| **ArgoCD** | https://argocd-0.localhost | ArgoCD Login |
| **OTEL Metrics** | https://otel-0.localhost | Basic Auth |
| **AlertManager** | https://alertmanager-0.localhost | Basic Auth |
| **Promtail Metrics** | https://promtail-0.localhost | Basic Auth |

**Note**: For localhost development, you may need to accept the self-signed TLS certificates in your browser.

Internal services (direct port access for internal communication):
- **MongoDB**: `localhost:27017`
- **Redis**: `localhost:6379`
- **Kafka Broker**: `localhost:9092`
- **Neo4j Bolt**: `localhost:7687`
- **Qdrant gRPC**: `localhost:6334`
- **OTEL Collector OTLP gRPC**: `localhost:4317`
- **OTEL Collector OTLP HTTP**: `localhost:4318`

## Environment Variable Reference

### Instance IDs
Each service has an `INSTANCE_ID` that allows running multiple instances:
- `INSTANCE_ID=0` (default, first instance)
- `INSTANCE_ID=1` (second instance, ports auto-incremented)

Port calculation: `final_port = base_port + (instance_id * 100)`

### Network Configuration
```bash
OBSERVABILITY_NETWORK=observability-network
DATA_NETWORK=data-network
MESSAGING_NETWORK=messaging-network
CICD_NETWORK=cicd-network
```

### Security
```bash
# Traefik Dashboard Authentication
TRAEFIK_BASIC_AUTH=admin:$$apr1$$8s7VW3ZZ$$xvtzQGXr5lGhCgHqJz4Kx1

# API Keys
API_KEY=changeme-secure-api-key-here

# TLS Configuration
ACME_EMAIL=admin@localhost
```

Generate htpasswd:
```bash
# Install apache2-utils if not available
sudo apt-get install apache2-utils

# Generate password hash
htpasswd -nb admin your_password_here
```

### Service-Specific

See `.env.template` for complete list of variables for each service including:
- Ports
- Credentials
- Resource limits
- Health check timeouts
- Paths and directories

## Port Management

All ports are centrally managed in `infrastructure/orchestrator/dynamicconfig/port_registry.yaml`.

To get a port programmatically:
```python
from infrastructure.orchestrator.base.port_manager import PortManager

pm = PortManager()
port = pm.get_port('grafana', instance_id=0, port_type='port')  # Returns 3000
```

## Network Security

See `config/network-security-policy.md` for detailed security architecture including:
- Network segmentation strategy
- Access control matrix
- TLS configuration
- Security headers
- Rate limiting
- IP whitelisting
- Production hardening recommendations

## Troubleshooting

### Port Conflicts
```bash
# Check if port is in use
sudo netstat -tulpn | grep :PORT_NUMBER

# Stop conflicting service
docker ps | grep PORT_NUMBER
docker stop CONTAINER_ID
```

### Network Issues
```bash
# Recreate networks
docker network rm observability-network data-network messaging-network cicd-network
bash scripts/create-networks.sh

# Inspect network
docker network inspect observability-network
```

### TLS Certificate Issues
```bash
# Check Traefik logs
docker logs traefik-instance-0

# Clear ACME certificates and restart
docker volume rm traefik-certs-0
docker-compose -f traefik-dynamic-docker.yaml --env-file ../../.env up -d --force-recreate
```

### Health Check Failures
```bash
# Check service logs
docker logs SERVICE-instance-0

# Check health status
docker inspect SERVICE-instance-0 | grep -A 20 Health
```

## Multi-Instance Deployment

To run multiple instances (e.g., for testing or HA):

```bash
# Set different instance ID
export PROMETHEUS_INSTANCE_ID=1
export PROMETHEUS_PORT=9190  # 9090 + (1 * 100)

docker-compose -f prometheus-dynamic-docker.yaml --env-file ../../.env up -d
```

Access at `https://prometheus-1.localhost`

## Production Deployment

### Before Production

1. **Change All Default Passwords**
   ```bash
   # Update .env with strong passwords
   GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
   MONGODB_ROOT_PASSWORD=$(openssl rand -base64 32)
   NEO4J_PASSWORD=$(openssl rand -base64 32)
   # ... etc
   ```

2. **Use Production TLS Certificates**
   ```bash
   # Remove staging CA server line from traefik-dynamic-docker.yaml
   # Or use custom certificates
   ```

3. **Enable Redis Password**
   ```bash
   REDIS_PASSWORD=$(openssl rand -base64 32)
   # Update redis command in yaml file
   ```

4. **Implement Kafka SASL**
   - Configure SASL/PLAIN or SASL/SCRAM
   - Update Kafka environment variables

5. **Restrict IP Whitelist**
   ```bash
   # Update in .env
   IP_WHITELIST=YOUR_OFFICE_IP/32,YOUR_VPN_IP/32
   ```

6. **Review Security Policy**
   - Read `config/network-security-policy.md`
   - Implement recommended hardening

### Kubernetes Deployment

For Kubernetes deployment:
1. Create ConfigMaps from environment variables (see `config/kubernete/examples/`)
2. Create Secrets for sensitive data
3. Apply NetworkPolicies
4. Deploy services
5. Configure Ingress with cert-manager

## Monitoring

### Metrics
- Prometheus scrapes all services (via prometheus.io.* labels)
- Traefik exposes metrics at `:8080/metrics`
- View in Grafana dashboards

### Logs
- All containers log to stdout/stderr
- Promtail collects Docker logs
- Loki aggregates logs
- Query in Grafana or Loki UI

### Traces
- OTEL Collector receives traces on ports 4317/4318
- Tempo stores traces
- View in Jaeger or Grafana

## Backup and Recovery

```bash
# Backup MongoDB
docker exec mongodb-instance-0 mongodump --out=/data/backup --username=admin --password=MongoPassword123! --authenticationDatabase=admin

# Backup Neo4j
docker exec neo4j-instance-0 neo4j-admin backup --backup-dir=/var/lib/neo4j/backup

# Backup configuration
cp infrastructure/orchestrator/.env infrastructure/orchestrator/.env.backup
```

## Support

For issues or questions:
1. Check service logs: `docker logs SERVICE-instance-0`
2. Review documentation in `config/network-security-policy.md`
3. Validate configuration: `docker-compose -f SERVICE.yaml --env-file ../../.env config`
4. Check port registry: `infrastructure/orchestrator/dynamicconfig/port_registry.yaml`

## Related Documentation

- [Network Security Policy](config/network-security-policy.md)
- [Port Registry](dynamicconfig/port_registry.yaml)
- [Implementation Plan](../../.gemini/antigravity/brain/.../implementation_plan.md)
