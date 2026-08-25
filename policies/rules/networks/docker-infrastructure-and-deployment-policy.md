# Docker Infrastructure & Microservice Deployment Policy

| Field | Value |
| --- | --- |
| **Policy ID** | `POL-NET-DOCKER-001` |
| **Status** | **Active / Enforced** |
| **Date** | 2026-08-25 |
| **Scope** | Platform Infrastructure (`packages/node/frontend-deployment`), Python Microservices (`packages/python/*`), Node Apps (`packages/node/*`) |

---

## 1. Executive Summary & Core Principle

To prevent data siloing, port collisions, and resource waste, **all shared infrastructure daemons (Kafka message brokers, Redis caches, OpenTelemetry Collectors, Tempo tracing engines, PostgreSQL, and Grafana visualizers) belong to a single Central Shared Platform Infrastructure Network (`llmobs-network`)**.

Individual microservice packages (`packages/python/*`, `packages/node/*`) MUST NOT spawn redundant local instances of message brokers or caching daemons in production/integration environments. All microservice containers attach to the shared `llmobs-network` and consume shared platform services via standard environment variables.

---

## 2. Shared Platform Infrastructure Port & Network Registry

The shared infrastructure stack is orchestrated via `packages/node/frontend-deployment/docker-compose.yml` on the shared Docker bridge network `llmobs-network`:

| Component Service | Container Name | Host Port Binding | Internal Network Endpoint | Purpose |
|---|---|---|---|---|
| **Traefik Gateway** | `frontend-traefik-gateway` | `31410` (HTTP), `31411` (Dashboard), `31419` (HTTPS) | `http://traefik:80` | Reverse proxy & SSL termination |
| **Redis Cache** | `frontend-redis` | `31413` | `redis:6379` | Micro-USD spend ledgers & API key TTL cache |
| **Kafka Broker** | `frontend-kafka` | `31414` | `kafka:9092` | Asynchronous span stream bus (`llm.spans.raw`) |
| **Grafana Visualizer** | `frontend-grafana` | `31415` | `http://grafana:3000` | Operational telemetry dashboards |
| **Tempo Tracing Engine** | `frontend-tempo` | `31416` | `http://tempo:3200` | Trace waterfall storage & query engine |
| **OTEL Collector (HTTP)** | `frontend-otel-collector` | `31417` | `http://otel-collector:4318` | OpenTelemetry OTLP HTTP receiver endpoint |
| **OTEL Collector (gRPC)** | `frontend-otel-collector` | `31418` | `otel-collector:4317` | OpenTelemetry OTLP gRPC receiver endpoint |

---

## 3. Architecture Blueprint (Shared Infrastructure vs Microservice Workers)

```mermaid
flowchart TD
    subgraph SharedInfra["CENTRAL PLATFORM INFRASTRUCTURE (packages/node/frontend-deployment)"]
        SharedKafka["frontend-kafka (Port 31414 / kafka:9092)\nTopic: llm.spans.raw"]
        SharedRedis["frontend-redis (Port 31413 / redis:6379)\nHINCRBY Spend Ledgers"]
        SharedOtel["frontend-otel-collector (Port 31417 / otel-collector:4318)\nOTLP Receiver"]
        SharedTempo["frontend-tempo (Port 31416 / tempo:3200)\nTrace Waterfall Engine"]
    end

    subgraph PythonMicroservices["PYTHON MICROSERVICES (packages/python/*)"]
        SDK["instrumentation-sdk (:8000)\nKAFKA_BOOTSTRAP_SERVERS=kafka:9092"]
        CostWorker["event-cost-worker (Daemon)\nKAFKA_BOOTSTRAP_SERVERS=kafka:9092"]
        NliWorker["nli-worker (Daemon)"]
        SloWorker["slo-burn-worker (Daemon)"]
    end

    subgraph NodeMicroservices["NODE / NEXT.JS APPLICATIONS (packages/node/*)"]
        WebApp["web-app (:3000)\nNEXT_PUBLIC_OTEL_EXPORTER=http://localhost:31417/v1/traces"]
    end

    SDK -->|Publish Spans| SharedKafka
    SharedKafka -->|Stream Batches| CostWorker
    SharedKafka -->|Stream Batches| NliWorker
    SharedKafka -->|Stream Batches| SloWorker
    CostWorker -->|Update Spend Counters| SharedRedis
    WebApp -->|Emit UI Traces| SharedOtel
    SharedOtel --> SharedTempo
```

---

## 4. Sub-Package Docker Deployment Rules

Every sub-package directory (`packages/{lang}/{package-name}/`) MUST adhere to the following rules:

### Rule 1: Build Directory Isolation (`build/`)
- `build/Dockerfile`: MUST compile and package application binaries only.
- `build/` files MUST NOT bundle PostgreSQL, Kafka, or Redis daemons inside the application container image.

### Rule 2: Deployment Directory Structure (`deploy/docker/`)
- `deploy/docker/docker-compose.yaml` (or `docker-compose.dev.yaml`):
  - MUST configure the application service container to join `llmobs-network` as an external network:
    ```yaml
    networks:
      llmobs-network:
        external: true
    ```
- Sub-package compose files MUST NOT instantiate duplicate Kafka brokers or Redis servers for production or integration testing environments.

### Rule 3: Environment Variable Defaults (`.env.example`)
- Every sub-package MUST provide `.env.example` referencing the shared infrastructure endpoints:
  ```env
  KAFKA_BOOTSTRAP_SERVERS=kafka:9092
  KAFKA_TOPIC=llm.spans.raw
  REDIS_URL=redis://redis:6379/0
  POSTGRES_URL=postgresql://admin:password@postgres:5432/llm_observability
  NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:31417/v1/traces
  ```

---

## 5. Non-Negotiable Compliance Checklist for CI/CD

1. **No Duplicate Kafka Brokers**: CI checks flag any `docker-compose.yaml` under `packages/` that defines image `apache/kafka` or `redpandadata/redpanda`.
2. **No Reserved Port Stealing**: Sub-packages must not bind host ports `31410` through `31419`.
3. **Shared Network Join**: All microservice compose configurations must declare `networks: llmobs-network: external: true`.
