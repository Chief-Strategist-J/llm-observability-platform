# Infrastructure Orchestrator - Technical Documentation

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
  - [Docker Compose](#docker-compose-deployment)
  - [Python API](#python-api-deployment)
  - [Temporal Workflows](#temporal-workflow-deployment)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Monitoring & Observability](#monitoring--observability)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Infrastructure Orchestrator provides a unified platform for deploying, managing, and monitoring containerized infrastructure services with comprehensive observability, security, and automation capabilities.

### Key Features

- **Centralized Configuration**: Single `.env` file for all service configurations
- **Port Management**: Dynamic port allocation with zero conflicts
- **Network Isolation**: Segmented networks for different service types
- **Security**: TLS encryption, authentication, rate limiting, IP whitelisting
- **Multi-Instance Support**: Run multiple instances of any service
- **Three Deployment Methods**: Docker Compose, Python API, or Temporal Workflows
- **Full Observability**: Metrics (Prometheus), Logs (Loki), Traces (Tempo/Jaeger)

### Supported Services

**Observability Stack:**
- Prometheus (Metrics)
- Grafana (Visualization)
- Loki (Logs Aggregation)
- Tempo (Distributed Tracing)
- Jaeger (Trace Visualization)
- OpenTelemetry Collector
- Promtail (Log Shipper)
- AlertManager (Alerting)
- Traefik (Reverse Proxy & Ingress)

**Data Layer:**
- MongoDB (Document Database)
- Redis (Cache & Message Broker)
- Neo4j (Graph Database)
- Qdrant (Vector Database)

**Messaging:**
- Kafka (Event Streaming)

**CI/CD:**
- ArgoCD Server & Repo Server

**Admin Tools:**
- MongoExpress (MongoDB UI)

---

## Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik                              │
│                    (Reverse Proxy)                           │
│              HTTPS Entry Point (Port 443)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┴──────────────┬──────────────┬────────────┐
       │                          │              │            │
┌──────▼────────┐      ┌─────────▼────┐  ┌──────▼───┐  ┌────▼─────┐
│ Observability │      │    Data      │  │ Messaging│  │  CI/CD   │
│   Network     │      │   Network    │  │  Network │  │  Network │
│ 172.20.0.0/16 │      │172.21.0.0/16 │  │172.22../16│ │172.23../16│
└───────────────┘      └──────────────┘  └──────────┘  └──────────┘
```

### Data Flow

```
Application → OTEL Collector → {Tempo (traces), Prometheus (metrics)}
                ↓
            Loki ← Promtail ← Docker Logs
                ↓
            Grafana (Unified Dashboard)
```

---

## Quick Start

### Prerequisites

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
# Navigate to orchestrator directory


# Copy environment template
cp .env.template .env

# Create required Docker networks (run this first, only once)
docker network create --driver bridge observability-network || true
docker network create --driver bridge data-network || true
docker network create --driver bridge messaging-network || true
docker network create --driver bridge cicd-network || true
docker network create --driver bridge temporal-network || true

cd infrastructure/orchestrator/config/docker
docker compose -f traefik-dynamic-docker.yaml up -d
cd ../..

cd infrastructure/orchestrator
docker compose -f temporal-orchestrator-compose.yaml up -d
cd ../..

source /home/j/live/dinesh/llm-chatbot-python/.venv/bin/activate

python infrastructure/orchestrator/workers/traefik_pipeline_worker.py

PYTHONPATH=/home/j/live/dinesh/llm-chatbot-python python infrastructure/orchestrator/trigger/common/tracing_pipeline_start.py
```

**Critical Variables to Update:**
```bash
# Generate secure auth
TRAEFIK_BASIC_AUTH=$(htpasswd -nb admin your_secure_password)
API_KEY=$(openssl rand -hex 32)

# Update passwords
GRAFANA_ADMIN_PASSWORD=changeme
MONGODB_ROOT_PASSWORD=changeme
NEO4J_PASSWORD=changeme
REDIS_PASSWORD=changeme

# TLS configuration
ACME_EMAIL=your-email@example.com
```

### 2. Create Networks

```bash
bash scripts/create-networks.sh
```

Creates isolated networks:
- `observability-network` (172.20.0.0/16) - Monitoring stack
- `data-network` (172.21.0.0/16) - Databases
- `messaging-network` (172.22.0.0/16) - Kafka
- `cicd-network` (172.23.0.0/16) - ArgoCD

### 3. Deploy Services

Choose your deployment method:
- [Docker Compose](#docker-compose-deployment) - Direct container management
- [Python API](#python-api-deployment) - Programmatic control
- [Temporal Workflows](#temporal-workflow-deployment) - Orchestrated deployments

---

## Deployment Methods

### Docker Compose Deployment

**Deploy Individual Services:**

```bash
cd infrastructure/orchestrator/config/docker

# Reverse Proxy (Deploy First)
docker-compose -f traefik-dynamic-docker.yaml --env-file ../../.env up -d

# Observability Stack
docker-compose -f prometheus-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f grafana-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f loki-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f tempo-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f jaeger-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f otel-collector-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f promtail-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f alertmanager-docker.yaml --env-file ../../.env up -d

# Databases
docker-compose -f mongodb-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f redis-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f neo4j-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f qdrant-dynamic-docker.yaml --env-file ../../.env up -d

# Messaging
docker-compose -f kafka-dynamic-docker.yaml --env-file ../../.env up -d

# Admin UIs
docker-compose -f mongoexpress-dynamic-docker.yaml --env-file ../../.env up -d

# CI/CD
docker-compose -f argocd-server-dynamic-docker.yaml --env-file ../../.env up -d
docker-compose -f argocd-repo-dynamic-docker.yaml --env-file ../../.env up -d
```

**Stop Services:**
```bash
docker-compose -f SERVICE-dynamic-docker.yaml --env-file ../../.env down
```

**Restart Services:**
```bash
docker-compose -f SERVICE-dynamic-docker.yaml --env-file ../../.env restart
```

**Delete Everything (Containers, Volumes, Images):**
```bash
docker-compose -f SERVICE-dynamic-docker.yaml --env-file ../../.env down --volumes --rmi all
```

---

### Python API Deployment

**Simple Container Management with Zero Code Duplication**

#### Installation

```bash
# Ensure you're in the project root
cd /home/j/live/dinesh/llm-chatbot-python

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

#### Basic Usage

```python
from infrastructure.orchestrator.base import YAMLContainerManager, ContainerState

# Initialize manager with YAML config path
manager = YAMLContainerManager(
    yaml_path="infrastructure/orchestrator/config/docker/mongodb-dynamic-docker.yaml",
    instance_id=0  # Optional: defaults to 0
)

# Start container (restarts if already running)
success = manager.start(restart_if_running=True)
print(f"Started: {success}")

# Check status
status = manager.get_status()
print(f"Status: {status.value}")  # "running", "stopped", "exited", etc.

# Restart
success = manager.restart()

# Stop (force kill)
success = manager.stop(force=True, timeout=10)

# Delete everything (containers, volumes, images)
success = manager.delete(
    remove_volumes=True,    # Remove named volumes
    remove_images=True,     # Remove container images
    remove_networks=False   # Keep shared networks
)
```

#### Advanced Usage with Custom Environment

```python
# Pass custom environment variables
env_vars = {
    "MONGODB_PORT": "27018",
    "MONGODB_ROOT_PASSWORD": "custom_password"
}

manager = YAMLContainerManager(
    yaml_path="infrastructure/orchestrator/config/docker/mongodb-dynamic-docker.yaml",
    instance_id=1,  # Second instance
    env_vars=env_vars
)

manager.start()
```

#### Multi-Instance Deployment

```python
# Deploy 3 Prometheus instances
for instance_id in range(3):
    manager = YAMLContainerManager(
        yaml_path="infrastructure/orchestrator/config/docker/prometheus-dynamic-docker.yaml",
        instance_id=instance_id
    )
    
    if manager.start():
        port = 9090 + (instance_id * 100)  # Auto-calculated
        print(f"Prometheus instance {instance_id} running on port {port}")
        print(f"Access at: https://prometheus-{instance_id}.localhost")
```

#### Complete Lifecycle Example

```python
from pathlib import Path
from infrastructure.orchestrator.base import YAMLContainerManager

# Path to config directory
CONFIG_DIR = Path("infrastructure/orchestrator/config/docker")

# Deploy full observability stack
services = [
    ("traefik", "traefik-dynamic-docker.yaml"),
    ("prometheus", "prometheus-dynamic-docker.yaml"),
    ("grafana", "grafana-dynamic-docker.yaml"),
    ("loki", "loki-dynamic-docker.yaml"),
]

managers = {}

# Start all services
for service_name, yaml_file in services:
    yaml_path = CONFIG_DIR / yaml_file
    manager = YAMLContainerManager(str(yaml_path), instance_id=0)
    
    if manager.start():
        print(f"✅ {service_name} started")
        managers[service_name] = manager
    else:
        print(f"❌ {service_name} failed to start")

# Check all statuses
for service_name, manager in managers.items():
    status = manager.get_status()
    print(f"{service_name}: {status.value}")

# Cleanup (optional)
# for manager in managers.values():
#     manager.delete(remove_volumes=True, remove_images=False)
```

#### Using Temporal Activities

All services have pre-built Temporal activities:

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyDeploymentWorkflow:
    @workflow.run
    async def run(self, params: dict) -> str:
        # Start MongoDB
        await workflow.execute_activity(
            "start_mongodb_activity",
            {"instance_id": 0},
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Start Redis
        await workflow.execute_activity(
            "start_redis_activity",
            {"instance_id": 0},
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return "Databases deployed successfully"
```

**Available Activities for Each Service:**
- `start_{service}_activity` - Start with auto-restart
- `stop_{service}_activity` - Force stop
- `restart_{service}_activity` - Restart
- `delete_{service}_activity` - Complete cleanup
- `get_{service}_status_activity` - Get current status

---

### Temporal Workflow Deployment

**Orchestrated Deployments with Retry Logic, Scheduling, and Monitoring**

#### Prerequisites

```bash
# Start Temporal Server (if not already running)
docker run -d -p 7233:7233 -p 8233:8233 temporalio/auto-setup:latest

# Temporal Web UI will be available at http://localhost:8233
```

#### Start Workers

```bash
cd infrastructure/orchestrator

# Start specific worker
python -m workers.kafka_mongodb_worker

# Or start all workers (in separate terminals)
python -m workers.alerting_pipeline_worker &
python -m workers.argocd_worker &
# ... etc
```

#### Trigger Workflows

**Using Python Triggers:**

```bash
cd infrastructure/orchestrator

# Deploy full observability stack
python trigger/common/logs_pipeline_start.py

# Deploy databases
python trigger/common/database_pipeline_start.py

# Deploy messaging
python trigger/common/kafka_mangodb_start.py

# Deploy tracing stack
python trigger/common/tracing_pipeline_start.py

# Deploy metrics stack
python trigger/common/metrics_pipeline_start.py

# Deploy alerting
python trigger/common/alerting_pipeline_start.py

# Deploy CI/CD
python trigger/common/argocd_start.py

# Deploy Traefik
python trigger/common/start_traefik_pipeline.py
```

**Using Python Client Directly:**

```python
import asyncio
from temporalio.client import Client

async def deploy_infrastructure():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Start workflow
    handle = await client.start_workflow(
        "LogsPipelineWorkflow",
        {"service_name": "loki"},
        id="logs-pipeline-deployment",
        task_queue="logs-pipeline-queue",
    )
    
    print(f"Workflow started: {handle.id}")
    print(f"Monitor at: http://localhost:8233")
    
    # Wait for result
    result = await handle.result()
    print(f"Result: {result}")

asyncio.run(deploy_infrastructure())
```

**Available Workflows:**

| Workflow | Description | Task Queue |
|----------|-------------|------------|
| `LogsPipelineWorkflow` | Loki + Promtail + Grafana | `logs-pipeline-queue` |
| `MetricsPipelineWorkflow` | Prometheus + Grafana | `metrics-pipeline-queue` |
| `TracingPipelineWorkflow` | Tempo + Jaeger + Grafana | `tracing-pipeline-queue` |
| `DatabasePipelineWorkflow` | Neo4j + Qdrant | `database-pipeline-queue` |
| `KafkaMangoDBDatabaseWorkflow` | Kafka + MongoDB + MongoExpress | `kafka-mongodb-queue` |
| `AlertingPipelineWorkflow` | AlertManager + Prometheus | `alerting-pipeline-queue` |
| `ArgoCDGitOpsWorkflow` | ArgoCD Server + Repo | `argocd-queue` |
| `TraefikWorkflow` | Traefik Reverse Proxy | `traefik-queue` |

**Environment Variables for Temporal:**

```bash
# Set in your shell or .env
export TEMPORAL_HOST=localhost:7233
export TEMPORAL_WEB_UI_URL=http://localhost:8233
export TEMPORAL_SERVICE_NAME=myservice
export TEMPORAL_WORKFLOW_NAME=MyWorkflow
export TEMPORAL_TASK_QUEUE=my-queue
```

---

## Configuration

### Environment Variables

**Port Configuration:**
```bash
# Instance ID (for multi-instance deployments)
MONGODB_INSTANCE_ID=0
REDIS_INSTANCE_ID=0

# Specific Ports (auto-calculated if not set)
MONGODB_PORT=27017
REDIS_PORT=6379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

**Network Configuration:**
```bash
OBSERVABILITY_NETWORK=observability-network
DATA_NETWORK=data-network
MESSAGING_NETWORK=messaging-network
CICD_NETWORK=cicd-network

# Network Subnets
OBSERVABILITY_SUBNET=172.20.0.0/16
DATA_SUBNET=172.21.0.0/16
MESSAGING_SUBNET=172.22.0.0/16
CICD_SUBNET=172.23.0.0/16
```

**Security Configuration:**
```bash
# Traefik Authentication
TRAEFIK_BASIC_AUTH=admin:$$apr1$$...

# Service Credentials
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=changeme
MONGODB_ROOT_USERNAME=admin
MONGODB_ROOT_PASSWORD=changeme
NEO4J_AUTH=neo4j/password
REDIS_PASSWORD=changeme

# API Security
API_KEY=your-api-key-here

# TLS/SSL
ACME_EMAIL=admin@localhost
```

**Resource Limits:**
```bash
# Memory Limits
PROMETHEUS_MEMORY_LIMIT=2g
GRAFANA_MEMORY_LIMIT=512m
MONGODB_MEMORY_LIMIT=1g

# CPU Limits
PROMETHEUS_CPU_LIMIT=2.0
GRAFANA_CPU_LIMIT=1.0
```

**Health Checks:**
```bash
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3
HEALTH_CHECK_START_PERIOD=40s
```

### Port Registry

Centralized port management in `dynamicconfig/port_registry.yaml`:

```python
from infrastructure.orchestrator.base.port_manager import PortManager

pm = PortManager()

# Get specific port
port = pm.get_port('grafana', instance_id=0, port_type='port')  # 3000

# Get all ports for a service
ports = pm.get_ports('kafka', instance_id=0)
# Returns: {'port': 9092, 'ui_port': 9093, ...}

# Check if port is available
is_available = pm.check_port_available(3000)

# Validate instance
valid, message = pm.validate_instance('prometheus', instance_id=5)
```

---

## API Reference

### YAMLContainerManager

Main class for container lifecycle management.

```python
class YAMLContainerManager:
    def __init__(
        self,
        yaml_path: str,
        instance_id: int = 0,
        env_vars: Optional[Dict[str, str]] = None
    )
```

**Methods:**

#### `start(restart_if_running: bool = True) -> bool`
Start container. If already running, restarts if `restart_if_running=True`.

**Returns:** `True` if successful, `False` otherwise.

**Example:**
```python
manager = YAMLContainerManager("config/docker/mongodb-dynamic-docker.yaml")
success = manager.start()  # Restarts if already running
```

#### `stop(force: bool = True, timeout: int = 10) -> bool`
Stop container.

**Parameters:**
- `force`: If `True`, uses kill (immediate). If `False`, graceful shutdown.
- `timeout`: Seconds to wait for graceful shutdown.

**Returns:** `True` if successful, `False` otherwise.

**Example:**
```python
manager.stop(force=True)  # Force kill
manager.stop(force=False, timeout=30)  # Graceful with 30s timeout
```

#### `restart() -> bool`
Restart container.

**Returns:** `True` if successful, `False` otherwise.

#### `delete(remove_volumes: bool = True, remove_images: bool = True, remove_networks: bool = False) -> bool`
Complete cleanup of container resources.

**Parameters:**
- `remove_volumes`: Remove named volumes.
- `remove_images`: Remove container images.
- `remove_networks`: Remove networks (use cautiously with shared networks).

**Returns:** `True` if successful, `False` otherwise.

**Example:**
```python
# Delete everything except networks
manager.delete(remove_volumes=True, remove_images=True, remove_networks=False)
```

#### `get_status() -> ContainerState`
Get current container state.

**Returns:** `ContainerState` enum value.

**Possible States:**
- `ContainerState.RUNNING` - Container is running
- `ContainerState.EXITED` - Container exited
- `ContainerState.CREATED` - Container created but not started
- `ContainerState.RESTARTING` - Container is restarting
- `ContainerState.PAUSED` - Container is paused
- `ContainerState.DEAD` - Container is dead
- `ContainerState.NOT_FOUND` - Container not found
- `ContainerState.UNKNOWN` - Unknown state

**Example:**
```python
status = manager.get_status()
if status == ContainerState.RUNNING:
    print("Container is running")
elif status == ContainerState.NOT_FOUND:
    print("Container not found")
```

### Logging

All operations include detailed LogQL-structured logging:

```python
# Logs include:
# - trace_id: Unique ID for operation tracing
# - service: Service name
# - instance_id: Instance number
# - duration_ms: Operation duration
# - command: Docker command executed
# - stdout/stderr: Command output
# - error_type/error_msg: Error details
```

**Query logs in Loki:**
```logql
{job="orchestrator"} |= "mongodb" | json | duration_ms > 1000
```

---

## Monitoring & Observability

### Service Access

**External Services (HTTPS via Traefik):**

| Service | URL | Authentication |
|---------|-----|----------------|
| Traefik Dashboard | https://traefik-0.localhost | Basic Auth |
| Grafana | https://grafana-0.localhost | Grafana Login |
| Prometheus | https://prometheus-0.localhost | Basic Auth |
| Loki | https://loki-0.localhost | Basic Auth |
| Tempo | https://tempo-0.localhost | Basic Auth |
| Jaeger | https://jaeger-0.localhost | None |
| Mongo Express | https://mongoexpress-0.localhost | Basic Auth |
| Neo4j Browser | https://neo4j-0.localhost | Neo4j Login |
| Qdrant UI | https://qdrant-0.localhost | None |
| ArgoCD | https://argocd-0.localhost | ArgoCD Login |
| OTEL Metrics | https://otel-0.localhost | Basic Auth |
| AlertManager | https://alertmanager-0.localhost | Basic Auth |

**Internal Services (Direct Port Access):**

| Service | Port | Protocol |
|---------|------|----------|
| MongoDB | 27017 | MongoDB Protocol |
| Redis | 6379 | Redis Protocol |
| Kafka | 9092 | Kafka Protocol |
| Neo4j Bolt | 7687 | Bolt Protocol |
| Qdrant gRPC | 6334 | gRPC |
| OTEL gRPC | 4317 | gRPC |
| OTEL HTTP | 4318 | HTTP |

### Metrics Collection

Prometheus automatically scrapes all services via service discovery:

```yaml
# Services expose metrics with labels:
prometheus.io.scrape: "true"
prometheus.io.port: "8080"
prometheus.io.path: "/metrics"
```

**Query Prometheus:**
```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes

# Service availability
up{job="traefik"}
```

### Log Aggregation

All container logs flow through: `Docker → Promtail → Loki → Grafana`

**Query logs in Loki:**
```logql
# All MongoDB logs
{container_name="mongodb-instance-0"}

# Errors in last hour
{job="orchestrator"} |= "error" | json | __timestamp__ > 1h

# Slow operations
{job="orchestrator"} | json | duration_ms > 5000
```

### Distributed Tracing

Application traces: `App → OTEL Collector → Tempo → Jaeger/Grafana`

**Send traces from your app:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter
exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# Create traces
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

### Alerting

Configure alerts in `config/prometheus/alerts.yml`:

```yaml
groups:
  - name: infrastructure
    rules:
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes > 1e9
        for: 5m
        annotations:
          summary: "High memory usage detected"
```

---

## Production Deployment

### Security Hardening

**1. Update All Passwords:**
```bash
# Generate secure passwords
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
MONGODB_ROOT_PASSWORD=$(openssl rand -base64 32)
NEO4J_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
API_KEY=$(openssl rand -hex 64)
```

**2. Enable Production TLS:**
```bash
# Edit traefik-dynamic-docker.yaml
# Remove or comment out the staging CA line:
# - "--certificatesresolvers.letsencrypt.acme.caserver=..."

# Use production Let's Encrypt
ACME_EMAIL=your-real-email@example.com
```

**3. Restrict Network Access:**
```bash
# Limit IP whitelist
IP_WHITELIST=YOUR_OFFICE_IP/32,YOUR_VPN_IP/32

# Disable unnecessary ports
# Comment out port mappings in YAML files for internal services
```

**4. Enable Authentication:**
```bash
# Redis
REDIS_PASSWORD=your-secure-password

# Kafka SASL
# Update kafka-dynamic-docker.yaml with SASL configuration
```

**5. Resource Limits:**
```bash
# Set appropriate limits based on load
PROMETHEUS_MEMORY_LIMIT=4g
GRAFANA_MEMORY_LIMIT=1g
MONGODB_MEMORY_LIMIT=2g
```

### High Availability

**Deploy Multiple Instances:**
```python
# Deploy 3 Prometheus instances
for i in range(3):
    manager = YAMLContainerManager(
        "config/docker/prometheus-dynamic-docker.yaml",
        instance_id=i
    )
    manager.start()
```

**Load Balancing:**
Configure Traefik for load balancing across instances.

### Kubernetes Migration

See `config/kubernetes/examples/` for Kubernetes manifests.

**Migration Steps:**
1. Export configurations to ConfigMaps
2. Create Secrets for sensitive data
3. Apply NetworkPolicies
4. Deploy with ArgoCD
5. Configure Ingress with cert-manager

---

## Troubleshooting

### Common Issues

**Port Conflicts:**
```bash
# Find process using port
sudo netstat -tulpn | grep :9090

# Kill process
kill -9 PID

# Or stop Docker container
docker ps | grep 9090
docker stop CONTAINER_ID
```

**Network Issues:**
```bash
# Recreate networks
docker network rm observability-network data-network messaging-network cicd-network
bash scripts/create-networks.sh

# Inspect network
docker network inspect observability-network

# Check containers on network
docker network inspect observability-network | grep -A 10 Containers
```

**Container Won't Start:**
```bash
# Check logs
docker logs mongodb-instance-0

# Check health
docker inspect mongodb-instance-0 | grep -A 20 Health

# Validate YAML
docker-compose -f mongodb-dynamic-docker.yaml --env-file ../../.env config

# Force recreate
docker-compose -f mongodb-dynamic-docker.yaml --env-file ../../.env up -d --force-recreate
```

**TLS Certificate Issues:**
```bash
# Check Traefik logs
docker logs traefik-instance-0

# Clear certificates
docker volume rm traefik-certs-0

# Restart Traefik
docker restart traefik-instance-0
```

**Python API Issues:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check container manager logs
from infrastructure.orchestrator.base import YAMLContainerManager
manager = YAMLContainerManager("config/docker/mongodb-dynamic-docker.yaml")
manager.start()
# Logs will show detailed operation info
```

**Temporal Workflow Issues:**
```bash
# Check worker logs
python -m workers.kafka_mongodb_worker  # Run in foreground

# Check Temporal Web UI
# Open http://localhost:8233

# Verify workflow is registered
temporal workflow show --workflow-id your-workflow-id
```

### Performance Optimization

**Reduce Log Volume:**
```yaml
# In docker-compose YAML
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Optimize Resource Usage:**
```bash
# Monitor resource usage
docker stats

# Adjust limits in .env
PROMETHEUS_MEMORY_LIMIT=2g  # Reduce if needed
PROMETHEUS_CPU_LIMIT=1.0
```

**Database Tuning:**
```bash
# MongoDB
# Adjust WiredTiger cache
# Edit mongodb-dynamic-docker.yaml:
# --wiredTigerCacheSizeGB=1

# Redis
# Set maxmemory
# Edit redis command in YAML:
# --maxmemory 512mb
```

---

## Backup & Recovery

### Backup Services

```bash
# Backup MongoDB
docker exec mongodb-instance-0 mongodump \
  --out=/data/backup \
  --username=admin \
  --password=$MONGODB_ROOT_PASSWORD \
  --authenticationDatabase=admin

# Copy backup to host
docker cp mongodb-instance-0:/data/backup ./mongodb-backup

# Backup Neo4j
docker exec neo4j-instance-0 neo4j-admin backup \
  --backup-dir=/var/lib/neo4j/backup

# Backup configuration
cp .env .env.backup
tar -czf config-backup.tar.gz config/
```

### Restore Services

```bash
# Restore MongoDB
docker cp ./mongodb-backup mongodb-instance-0:/data/restore
docker exec mongodb-instance-0 mongorestore \
  --dir=/data/restore \
  --username=admin \
  --password=$MONGODB_ROOT_PASSWORD \
  --authenticationDatabase=admin

# Restore configuration
tar -xzf config-backup.tar.gz
cp .env.backup .env
```

---

## Related Documentation

- [Network Security Policy](config/network-security-policy.md)
- [Port Registry](dynamicconfig/port_registry.yaml)
- [Base Container Activity API](base/base_container_activity.py)
- [Temporal Workflows](workflows/)
- [Activity Reference](activities/configurations_activity/)

---

## Support & Contributing

**Issues or Questions:**
1. Check container logs: `docker logs SERVICE-instance-0`
2. Review this documentation
3. Validate configuration: `docker-compose -f SERVICE.yaml --env-file ../../.env config`
4. Check port registry: `dynamicconfig/port_registry.yaml`

**For Developers:**
- All container management uses `YAMLContainerManager` base class
- Add new services by creating YAML configs and activity files
- Follow the existing patterns in `activities/configurations_activity/`
- Use LogQL structured logging for all operations

---

**Last Updated:** 2025-11-28  
**Version:** 2.0.0
