
## Quick Start

### Prerequisites

```bash
# Ensure you're in the project root
cd /home/j/live/dinesh/llm-chatbot-python

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

```bash
# Install Docker & Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 1.29

# Install Python (for API/Temporal)
python3 --version  # >= 3.10

# Install Apache Utils (for password generation)
sudo apt-get install apache2-utils
```

### 1. Setup Environment

```bash

cp .env.template .env


docker network create --driver bridge observability-network || true
docker network create --driver bridge data-network || true
docker network create --driver bridge messaging-network || true
docker network create --driver bridge cicd-network || true
docker network create --driver bridge temporal-network || true


cd infrastructure/orchestrator/config/docker/temporal
docker-compose -f temporal-orchestrator-compose.yaml up -d
cd ../../../../..

source /home/j/live/dinesh/llm-chatbot-python/.venv/bin/activate

# Setup service worker
python infrastructure/orchestrator/workers/service_setup_worker.py

python infrastructure/orchestrator/trigger/setup/start_mongodb.py

```



- **Mongo Express**: https://scaibu.mongoexpress/
username: admin
password: MongoExpressPassword123!

## 📍 Access Services

- **Traefik Dashboard**: http://traefik-0.localhost:13101/dashboard/
- **Kafka UI**: https://scaibu.kafka-ui/

- **Grafana**: https://grafana-0.localhost
- **Prometheus**: https://prometheus-0.localhost
- **Loki**: https://loki-0.localhost
- **Tempo**: https://tempo-0.localhost
- **Jaeger**: https://jaeger-0.localhost
- **Mongo Express**: https://mongoexpress-0.localhost
- **Neo4j Browser**: https://neo4j-0.localhost
- **Qdrant UI**: https://qdrant-0.localhost
- **ArgoCD**: https://argocd-0.localhost
- **OTEL Metrics**: https://otel-0.localhost
- **AlertManager**: https://alertmanager-0.localhost

