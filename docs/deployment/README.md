# Deployment Guide

## Quick Start

### Start All Services
```bash
# Start infrastructure and all services
docker-compose up -d
```

### Start Specific Services
```bash
# Start only databases
docker-compose -f infrastructure/databases/docker-compose.databases.yml --profile databases up -d

# Start kg-service with databases
docker-compose -f infrastructure/databases/docker-compose.databases.yml --profile databases -f service/kg-service/docker-compose.yml up -d

# Start rag-service with databases
docker-compose -f infrastructure/databases/docker-compose.databases.yml --profile databases -f service/rag-service/docker-compose.yml up -d
```

## Environment Variables

Create a `.env` file:
```bash
# Database credentials
NEO4J_AUTH=neo4j/your_password_here

# Network configuration
DATABASE_SUBNET=172.26.0.0/16

# Kafka brokers
KAFKA_BROKERS=kafka:9092
```

## Service Profiles

Use Docker profiles for conditional activation:

- `--profile databases`: Start Neo4j and Qdrant
- `--profile ai-proxy`: Start ai-proxy-service
- `--profile kg-service`: Start kg-service
- `--profile rag-service`: Start rag-service
- `--profile n8n-service`: Start automation-n8n-service

## Monitoring

Access monitoring tools:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Kafka UI**: http://localhost:8080

## Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs kg-service
```

### Restart Services
```bash
# Restart specific service
docker-compose restart kg-service

# Restart all
docker-compose restart
```

See CHANGELOG.md for detailed change history.
