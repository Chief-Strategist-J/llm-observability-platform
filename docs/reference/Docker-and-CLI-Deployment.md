# Docker & CLI Deployment

The SDK ships with an **all-in-one container image** that hosts the FastAPI api, Grafana dashboards, Prometheus, and Tempo into a single container context. This setup enables quick local development and testing with a single command.

---

## All-in-One Architecture

```
           [ llm-observe start ] or [ docker run ]
                        │
                        ▼
            [ Docker Container Context ]
  ┌─────────────────────┼─────────────────────┬─────────────────────┐
  ▼                     ▼                     ▼                     ▼
[FastAPI API]     [Prometheus]             [Tempo]              [Grafana]
  Port 8002         Port 9090             Port 4317             Port 3002
 (REST Spans)    (Scrapes Metrics)     (Ingests Traces)     (Pre-built UI)
```

---

## `llm-observe` CLI

The `llm-observe` utility is installed globally with `pip install instrumentation-sdk`.

### Commands

#### Start the Stack
Spins up the container with default ports:
```bash
llm-observe start
```

| Service | Port |
|---|---|
| FastAPI API | `8002` |
| Grafana | `3002` |
| Prometheus | `9090` |
| OTLP gRPC | `4317` |

To override default ports:
```bash
llm-observe start \
  --name my-obs-stack \
  --api-port 8010 \
  --grafana-port 3010 \
  --otlp-port 4320 \
  --prometheus-port 9095
```

#### Check Status
```bash
llm-observe status
```
```
Observability stack 'instrumentation-api-allinone': Running
```

#### Stop the Stack
```bash
llm-observe stop
```

---

## Docker — Direct Run

You can run the container image directly via the Docker CLI:

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

### Available Image Tags

| Tag | Intended Use |
|---|---|
| `latest` / `stable` | Production-ready stable builds |
| `unstable` | Bleeding-edge master builds |
| `v1.8.2` | Version-pinned builds |

---

## Layer 3 Evaluator Ports (Microservices)

In addition to the core API and metrics telemetry stack, the evaluation layer runs specialized microservices:

| Microservice | Default Port | Docker Image |
|---|---|---|
| **Semantic Coherence Scorer** | `8005` | `chiefj/semantic-coherence:latest` |
| **Faithfulness Scorer** | `8006` | `chiefj/faithfulness:latest` |
| **Toxicity Scorer** | `8007` | `chiefj/toxicity:latest` |

---

## Docker Compose — Development Stack

For contributors wanting to run the API alongside ClickHouse, Redis, PostgreSQL, and Kafka backends:

```bash
docker compose \
  -f packages/python/instrumentation-sdk/deploy/docker/docker-compose.dev.yaml \
  up instrumentation-api
```

### Dev Services & Ports

| Service | Port | Purpose |
|---|---|---|
| `instrumentation-api` | `8001` | Hot-reload FastAPI API |
| `PostgreSQL` | `5435` | Relational storage & pgvector |
| `ClickHouse` | `8123` | Columnar analytics data |
| `Redis` | `6380` | Caching and task queues |
| `Kafka` | `9094` | High-throughput ingestion stream |

---

## Verification Checks

After starting the stack, verify that services are healthy:

```bash
# Check API health
curl http://localhost:8002/v1/metrics/health

# Trigger a test trace
curl -X POST http://localhost:8002/v1/instrumentation/test-call \
  -H "Content-Type: application/json" \
  -d '{"method": "httpx", "provider": "openai"}'
```

---

## Next Steps

- [Config Files Reference](Config-Files-Reference.md) - Adjust scrape intervals, pricing lists, and scan targets.
- [REST Management API](REST-Management-API.md) - Full HTTP endpoints mapping.
