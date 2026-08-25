# Universal Docker Infrastructure & Service Deployment Policy

| Field | Value |
| --- | --- |
| **Policy ID** | `POL-NET-DOCKER-001` |
| **Status** | **Active / Enforced** |
| **Date** | 2026-08-25 |
| **Scope** | Universal Platform Monorepo (`packages/python/*`, `packages/node/*`, `packages/go/*`, `packages/java/*`, `packages/rust/*`, `packages/dart/*`, `packages/swift/*`, `packages/kotlin/*`) |

---

## 1. Executive Summary & Core Architectural Principle

Platform infrastructure separates **Centralized Infrastructure-Level Services** from **Microservice-Owned Databases**:

1. **Centralized Infrastructure Services (`packages/configs/llm-obs-infra`)**:
   - Infrastructure-level services (**Kafka message brokers, Redis caches/ledgers, OpenTelemetry Collectors, Tempo tracing engines, ClickHouse analytics stores, Traefik gateways, and Grafana dashboards**) are **CENTRALIZED** on the `llmobs-network` bridge.
   - Microservices MUST NOT spawn duplicate Kafka brokers or Redis caches.

2. **Decoupled Database-per-Service Rule (`packages/{lang}/{package-name}`)**:
   - Databases follow the strict **Database-per-Service** architectural pattern.
   - Each microservice package owns and maintains its **dedicated database schema and database instance** (e.g. `alert-engine` owns `ewma_db`, `slo-burn-worker` owns `slo_db`, `event-cost` owns `cost_ledger_db`).
   - Microservices MUST NOT share database instances or cross-query other microservice databases directly.

---

## 2. Standardized Service Naming & Port Registry (`llmobs-*`)

The central shared infrastructure stack is orchestrated via `packages/configs/llm-obs-infra/docker-compose.yml` on `llmobs-network` using standardized `llmobs-*` service names:

| Service Name | Container Name | Host Port Binding | Internal Network Endpoint | Core Service Purpose |
|---|---|---|---|---|
| **`llmobs-traefik`** | `llmobs-traefik-gateway` | `31410` (HTTP)<br>`31411` (Dashboard)<br>`31419` (HTTPS) | `http://llmobs-traefik:80` | Reverse proxy, SSL termination & rate limiting |
| **`llmobs-redis`** | `llmobs-redis-ledger` | `31413` | `llmobs-redis:6379` | Spend ledgers, API key TTL cache & atomic counters |
| **`llmobs-kafka`** | `llmobs-kafka-broker` | `31414` | `llmobs-kafka:9092` | Event stream bus (`llm.spans.raw` & DLQ topics) |
| **`llmobs-grafana`** | `llmobs-grafana-portal` | `31415` | `http://llmobs-grafana:3000` | Operational telemetry dashboards |
| **`llmobs-tempo`** | `llmobs-tempo-tracing` | `31416` | `http://llmobs-tempo:3200` | Trace waterfall storage & query engine |
| **`llmobs-otel-collector`** | `llmobs-otel-collector` | `31417` (HTTP)<br>`31418` (gRPC) | `http://llmobs-otel-collector:4318`<br>`llmobs-otel-collector:4317` | OpenTelemetry OTLP receiver endpoint |
| **`llmobs-alloydb`** | `llmobs-alloydb-db` | `31420` | `llmobs-alloydb:5432` | Partitioned span store & relational AlloyDB engine |
| **`llmobs-clickhouse`** | `llmobs-clickhouse-analytics` | `8123` (HTTP)<br>`9000` (Native) | `http://llmobs-clickhouse:8123` | High-throughput columnar analytics engine |

---

## 3. Exhaustive Platform Configuration Dictionary

All services across Python, Node, Go, Java, Rust, Dart, and Kotlin MUST consume these exact environment variables:

### 3.1 Messaging & Event Bus Configuration (Kafka)
```env
KAFKA_BOOTSTRAP_SERVERS=llmobs-kafka:9092
KAFKA_CONSUMER_GROUP=event-cost-worker-group
KAFKA_TOPIC=llm.spans.raw
KAFKA_DLQ_TOPIC=llm.spans.raw.dlq
KAFKA_NUM_PARTITIONS=3
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
```

### 3.2 Cache & Spend Ledger Configuration (Redis)
```env
REDIS_URL=redis://:llmobs_redis_s3cret_2024@llmobs-redis:6379/0
REDIS_HOST=llmobs-redis
REDIS_PORT=6379
REDIS_PASSWORD=llmobs_redis_s3cret_2024
REDIS_MAX_MEMORY=256mb
REDIS_EVICTION_POLICY=allkeys-lru
```

### 3.3 Relational & Columnar Database Configuration (AlloyDB / ClickHouse)
```env
ALLOYDB_URL=postgresql://admin:password@llmobs-alloydb:5432/llm_observability
ALLOYDB_HOST=llmobs-alloydb
ALLOYDB_PORT=5432
ALLOYDB_USER=admin
ALLOYDB_PASSWORD=password
ALLOYDB_DB=llm_observability
POSTGRES_URL=postgresql://admin:password@llmobs-alloydb:5432/llm_observability

CLICKHOUSE_URL=http://llmobs-clickhouse:8123
CLICKHOUSE_HOST=llmobs-clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=llm_telemetry_analytics
```

### 3.4 Telemetry & Distributed Tracing Configuration (OTEL / Tempo)
```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://llmobs-otel-collector:4318
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://llmobs-otel-collector:4318/v1/traces
NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:31417/v1/traces
TEMPO_ENDPOINT=http://llmobs-tempo:3200
```

### 3.5 Ingestion API & Gateway Configuration (Traefik)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
TRAEFIK_ENTRYPOINT_HTTP=:80
TRAEFIK_ENTRYPOINT_HTTPS=:443
TRAEFIK_DASHBOARD_RULE=Host(`llmobs.gateway`) || Host(`gateway.llmobs.local`)
```

---

## 4. Architecture Blueprint (Universal Shared Stack vs Microservice Workers)

```mermaid
flowchart TD
    subgraph CentralInfra["CENTRAL PLATFORM INFRASTRUCTURE (llmobs-network)"]
        SharedKafka["llmobs-kafka (Port 31414 / llmobs-kafka:9092)\nTopic: llm.spans.raw"]
        SharedRedis["llmobs-redis (Port 31413 / llmobs-redis:6379)\nHINCRBY Spend Ledgers"]
        SharedOtel["llmobs-otel-collector (Port 31417 / llmobs-otel-collector:4318)\nOTLP Receiver"]
        SharedTempo["llmobs-tempo (Port 31416 / llmobs-tempo:3200)\nTrace Waterfall Engine"]
        SharedDB[("llmobs-postgres (Port 31420) & llmobs-clickhouse (Port 8123)")]
    end

    subgraph PythonServices["PYTHON WORKSPACES (packages/python/*)"]
        SDK["instrumentation-sdk (:8000)\nKAFKA_BOOTSTRAP_SERVERS=llmobs-kafka:9092"]
        CostWorker["event-cost-worker (Daemon)\nKAFKA_BOOTSTRAP_SERVERS=llmobs-kafka:9092"]
        NliWorker["nli-worker (Daemon)"]
        SloWorker["slo-burn-worker (Daemon)"]
    end

    subgraph NodeServices["NODE WORKSPACES (packages/node/*)"]
        WebApp["web-app (:3000)\nNEXT_PUBLIC_OTEL_EXPORTER=http://localhost:31417/v1/traces"]
    end

    subgraph PolyglotServices["POLYGLOT WORKSPACES (Go / Rust / Java)"]
        GoService["packages/go/* services"]
        RustService["packages/rust/* services"]
        JavaService["packages/java/* services"]
    end

    SDK -->|Publish Spans| SharedKafka
    SharedKafka -->|Stream Batches| CostWorker
    SharedKafka -->|Stream Batches| NliWorker
    SharedKafka -->|Stream Batches| SloWorker
    PolyglotServices -->|Stream Spans| SharedKafka
    CostWorker -->|Update Spend Counters| SharedRedis
    CostWorker -->|Insert Spans| SharedDB
    WebApp -->|Emit UI Traces| SharedOtel
    SharedOtel --> SharedTempo
    WebApp -->|Query Analytics| SharedDB
```

---

## 5. Sub-Package Docker Deployment Rules

Every sub-package directory across ALL languages (`packages/{lang}/{package-name}/`) MUST adhere to the following rules:

### Rule 1: Build Directory Isolation (`build/`)
- `build/Dockerfile`: MUST compile and package application binaries only.
- `build/` Dockerfiles MUST NOT bundle PostgreSQL, Kafka, or Redis daemons inside the application container image.

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
- Every sub-package MUST provide `.env.example` referencing the standardized `llmobs-*` shared infrastructure endpoints defined in Section 3.

---

## 6. Non-Negotiable Compliance Checklist for CI/CD

1. **No Duplicate Kafka Brokers**: CI checks flag any `docker-compose.yaml` under `packages/` that defines image `apache/kafka` or `redpandadata/redpanda`.
2. **No Reserved Port Stealing**: Sub-packages must not bind host ports `31410` through `31420`.
3. **Standardized Service Naming**: Network endpoints MUST use `llmobs-*` hostnames (`llmobs-kafka`, `llmobs-redis`, `llmobs-postgres`, `llmobs-otel-collector`).
4. **Shared Network Join**: All microservice compose configurations must declare `networks: llmobs-network: external: true`.
