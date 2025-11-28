# Quick Start: Centralized Configuration

## 🚀 Get Started in 3 Steps

### 1. Configure Environment
```bash
# Copy template and edit
cp infrastructure/orchestrator/.env.template infrastructure/orchestrator/.env

# Update these values in .env:
# - TRAEFIK_BASIC_AUTH (generate with: htpasswd -nb admin password)
# - All passwords (Grafana, MongoDB, Neo4j, etc.)
# - ACME_EMAIL for TLS certificates
```

### 2. Create Networks
```bash
cd infrastructure/orchestrator
bash scripts/create-networks.sh
```

### 3. Deploy Services
```bash
cd config/docker

# Start Traefik (reverse proxy)
docker-compose -f traefik-dynamic-docker.yaml --env-file ../../.env up -d

# Start your services
docker-compose -f grafana-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f prometheus-dynamic-docker.yaml --env-file ../../.env up -d
# ... etc
```

## 📍 Access Services

All services available at `https://SERVICE-0.localhost`:

- **Grafana**: https://grafana-0.localhost
- **Prometheus**: https://prometheus-0.localhost  
- **Traefik Dashboard**: https://traefik-0.localhost
- **More**: See [README.md](file:///home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/README.md)

## 📚 Documentation

- **Full Guide**: [README.md](file:///home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/README.md)
- **Security**: [network-security-policy.md](file:///home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/config/network-security-policy.md)
- **Walkthrough**: [walkthrough.md](file:///home/j/.gemini/antigravity/brain/807ac149-2182-48f1-9899-358109b1e2ec/walkthrough.md)

## 🔐 Security Features

✅ TLS encryption (HTTPS)
✅ Basic authentication
✅ Rate limiting
✅ Network isolation
✅ Security headers

## ✨ What's New

- **Centralized `.env`**: All config in one place
- **Port management**: No conflicts, managed via port_registry.yaml
- **Traefik routing**: All external services via HTTPS
- **Network isolation**: 4 isolated networks (observability, data, messaging, cicd)
- **Security**: TLS, auth, headers, rate limiting

## 🛠️ Troubleshooting

```bash
# Check logs
docker logs SERVICE-instance-0

# Validate config
docker-compose -f SERVICE.yaml --env-file ../../.env config

# Recreate networks
docker network rm observability-network data-network messaging-network cicd-network
bash scripts/create-networks.sh
```

## 📊 Services Summary

**17 services** configured:
- **Observability** (8): Prometheus, Grafana, Loki, Tempo, Jaeger, OTEL, Promtail, AlertManager
- **Databases** (5): MongoDB, Mongo Express, Redis, Neo4j, Qdrant
- **Messaging** (1): Kafka
- **CI/CD** (2): ArgoCD Server, ArgoCD Repo
- **Routing** (1): Traefik

All use centralized `.env` configuration! 🎉
