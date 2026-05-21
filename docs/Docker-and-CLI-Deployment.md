# Docker & CLI Deployment

The SDK ships an **all-in-one container** that bundles the FastAPI API, Grafana, Prometheus, and Tempo into a single image — one command to get a fully wired observability stack.

---

## `llm-observe` CLI

After `pip install instrumentation-sdk`, the `llm-observe` command is available globally.

### Start

```bash
llm-observe start
```

Launches the stack with default ports:

| Service | Default Port |
|---|---|
| FastAPI API | `8002` |
| Grafana | `3002` |
| OTLP gRPC | `4317` |
| Prometheus | `9090` |

### Custom Ports

```bash
llm-observe start \
  --name my-obs \
  --api-port 8010 \
  --grafana-port 3010 \
  --otlp-port 4320 \
  --prometheus-port 9095
```

### Status

```bash
llm-observe status
```
```
Observability stack 'instrumentation-api-allinone': Running
```

### Stop

```bash
llm-observe stop
```
```
Stopping observability stack 'instrumentation-api-allinone'...
Removing container 'instrumentation-api-allinone'...
Observability stack stopped and removed successfully.
```

### Custom Image / Tag

```bash
llm-observe start --image chiefj/instrumentation-sdk-api --tag v1.7.2
```

---

## Docker — Direct

### Pull and Run

```bash
docker pull chiefj/instrumentation-sdk-api:latest

docker run -d \
  -p 8002:8000 \
  -p 3002:3000 \
  -p 4317:4317 \
  -p 9090:9090 \
  -p 9464:9464 \
  --name instrumentation-api-allinone \
  chiefj/instrumentation-sdk-api:latest
```

### With Environment Variables

```bash
docker run -d \
  -p 8002:8000 \
  -p 3002:3000 \
  -p 4317:4317 \
  -p 9090:9090 \
  -e DEPLOYMENT_ENV=production \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e EMBEDDING_WORKER_URL=http://embedding-service:8080 \
  --name instrumentation-api \
  chiefj/instrumentation-sdk-api:latest
```

### Available Tags

| Tag | Use |
|---|---|
| `latest` | Latest stable |
| `stable` | Same as latest |
| `unstable` | Latest build (may include unreleased features) |
| `v1.7.2` | Pinned version |

---

## Docker Compose — Development

Full local stack with Kafka, PostgreSQL, ClickHouse, and Redis:

```bash
docker compose \
  -f packages/python/instrumentation-sdk/deploy/docker/docker-compose.dev.yaml \
  up instrumentation-api
```

The dev container mounts source code and enables hot-reload via uvicorn `--reload`.

Services started:

| Service | Port |
|---|---|
| instrumentation-api (hot-reload) | `8001` |
| Kafka | `9094` |
| Zookeeper | `2182` |
| PostgreSQL + pgvector | `5435` |
| ClickHouse | `9001` / `8123` |
| Redis | `6380` |

---

## Docker Compose — Testing

```bash
docker compose \
  -f packages/python/instrumentation-sdk/deploy/docker/docker-compose.test.yaml \
  up --abort-on-container-exit
```

Runs the full pytest suite inside the container including contract, integration, and unit tests.

---

## Verify After Start

```bash
# Health check — API
curl http://localhost:8002/v1/metrics/health

# Trigger a test span
curl -X POST http://localhost:8002/v1/instrumentation/test-call \
  -H "Content-Type: application/json" \
  -d '{"method": "httpx", "provider": "openai"}'

# Open Grafana
open http://localhost:3002
# Credentials: admin / admin
```

---

## Restart After Config Changes

Most config files are read at startup — a restart is required after editing them:

```bash
docker restart instrumentation-sdk-api
```

Exception: Grafana dashboard JSON files (`build/dashboards/*.json`) are hot-reloaded every 30 seconds — no restart needed.

| File changed | Action |
|---|---|
| `config/model_prices.yaml` | Restart container |
| `config/patterns.yaml` | Restart container |
| `build/grafana-datasource.yaml` | Restart container |
| `build/prometheus.yml` | Restart container |
| `build/tempo-config.yaml` | Restart container |
| `build/dashboards/*.json` | Auto hot-reloaded ✅ |

---

## Build from Source

```bash
cd packages/python/instrumentation-sdk

# Build
docker build -f build/Dockerfile -t my-instrumentation-sdk .

# Run
docker run -d -p 8002:8000 -p 3002:3000 --name my-sdk my-instrumentation-sdk
```

### Deploy to Docker Hub

```bash
DOCKER_PAT=<your-pat> ./scripts/deploy_docker.sh
```

This builds and pushes tags: `latest`, `stable`, `unstable`, and the version tag from `pyproject.toml`.

---

## Next: [Config Files Reference](Config-Files-Reference)
