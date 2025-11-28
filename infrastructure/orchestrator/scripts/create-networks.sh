# Docker Networks Configuration Script
# Creates all required isolated networks for the orchestr infrastructure

# Usage: bash create-networks.sh

echo "Creating Docker networks for orchestrator infrastructure..."

# Observability Network (Prometheus, Grafana, Loki, Tempo, Jaeger, OTEL, Promtail, AlertManager)
docker network create \
  --driver bridge \
  --subnet ${OBSERVABILITY_SUBNET:-172.20.0.0/16} \
  --opt com.docker.network.bridge.name=obs_net \
  observability-network 2>/dev/null && echo "✓ Created observability-network" || echo "ℹ observability-network already exists"

# Data Network (MongoDB, Redis, Neo4j, Qdrant)
docker network create \
  --driver bridge \
  --subnet ${DATA_SUBNET:-172.21.0.0/16} \
  --opt com.docker.network.bridge.name=data_net \
  data-network 2>/dev/null && echo "✓ Created data-network" || echo "ℹ data-network already exists"

# Messaging Network (Kafka)
docker network create \
  --driver bridge \
  --subnet ${MESSAGING_SUBNET:-172.22.0.0/16} \
  --opt com.docker.network.bridge.name=msg_net \
  messaging-network 2>/dev/null && echo "✓ Created messaging-network" || echo "ℹ messaging-network already exists"

# CI/CD Network (ArgoCD)
docker network create \
  --driver bridge \
  --subnet ${CICD_SUBNET:-172.23.0.0/16} \
  --opt com.docker.network.bridge.name=cicd_net \
  cicd-network 2>/dev/null && echo "✓ Created cicd-network" || echo "ℹ cicd-network already exists"

echo ""
echo "Network creation complete!"
echo ""
echo "Networks created:"
docker network ls | grep -E "observability-network|data-network|messaging-network|cicd-network"
