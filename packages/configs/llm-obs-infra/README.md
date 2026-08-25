# Central Platform Infrastructure — Specification & Architecture Reference

> **Directory**: `packages/configs/llm-obs-infra`  
> **Version**: 2.0.0 (Production Core Stack)  
> **Network Bridge**: `llmobs-network`  
> **Database Engine Standard**: Google Cloud AlloyDB Omni (`google/alloydbomni:15`)  

---

## 1. High-Level Design (HLD) Architecture

The central platform infrastructure consolidates all core messaging, caching, workflow execution, database storage, and telemetry pipelines into a single high-performance container topology.

```mermaid
flowchart TD
    subgraph Clients["CLIENT APPLICATIONS & INGESTION"]
        PythonSDK["packages/python/instrumentation-sdk\n(FastAPI Ingestion Server :8000)"]
        NextJSFrontend["packages/node/web-app\n(Next.js Web Portal :3000)"]
    end

    subgraph ControlPlane["1. CONTROL & INGRESS PLANE"]
        TraefikGateway["llmobs-traefik (Traefik v3.7)\nPorts: 31410 (HTTP), 31411 (Dashboard), 31419 (HTTPS)\nReverse Proxy, TLS Termination & Security Rate Limiting"]
    end

    subgraph MessagingPlane["2. MESSAGING & WORKFLOW PLANE"]
        KafkaBroker["llmobs-kafka (Apache Kafka KRaft)\nPorts: 31414 (Host), 9092 (Internal)\nReal-time Event Streaming & Topic Partitioning"]
        TemporalEngine["llmobs-temporal (Temporal v1.24.2)\nPorts: 7233 (gRPC), 8088 (UI)\nDurable Execution & Saga Orchestration"]
    end

    subgraph DataPlane["3. STORAGE & CACHING PLANE"]
        AlloyDB["llmobs-alloydb (Google AlloyDB Omni 15)\nPorts: 31420 (Host), 5432 (Internal)\nTransactional Metadata & Relational Storage"]
        ClickHouse["llmobs-clickhouse (ClickHouse v24.8 Alpine)\nPorts: 8123 (HTTP), 9000 (Native Protocol)\nColumnar Span Telemetry & Log Analytics"]
        RedisLedger["llmobs-redis (Redis v7 Alpine)\nPorts: 31413 (Host), 6379 (Internal)\nMicro-USD Cost Ledger & API Key TTL Cache"]
    end

    subgraph ObservabilityPlane["4. TELEMETRY & OBSERVABILITY PLANE"]
        OtelCollector["llmobs-otel-collector (OpenTelemetry Contrib)\nPorts: 31417 (HTTP 4318), 31418 (gRPC 4317)\nOTLP Ingestion & Attribute Enrichment"]
        TempoTracing["llmobs-tempo (Grafana Tempo)\nPorts: 31416 (Host 3200), 4317 (gRPC)\nDistributed Trace Waterfall Storage"]
        GrafanaPortal["llmobs-grafana (Grafana Portal)\nPorts: 31415 (Host 3000)\nUnified Dashboards & Data Explorer"]
    end

    subgraph MicroserviceWorkers["5. ASYNCHRONOUS WORKER DAEMONS"]
        CostWorker["packages/python/event-cost-worker\n(Async Financial Spend Consumer)"]
        NliWorker["packages/python/nli-worker\n(LLM Evaluation & Hallucination Worker)"]
        QualityWorker["packages/python/quality-baseline-worker\n(Quality Baseline Recomputation Daemon)"]
    end

    PythonSDK -->|Publish Spans| KafkaBroker
    KafkaBroker -->|Stream Batches| CostWorker
    KafkaBroker -->|Stream Batches| NliWorker

    CostWorker -->|HINCRBY Micro-USD| RedisLedger
    CostWorker -->|Bulk Insert Spans| ClickHouse
    QualityWorker -->|Read Quality Scores| AlloyDB
    QualityWorker -->|Write Daily Rollup| ClickHouse

    TemporalEngine -->|State Persistence| AlloyDB
    NextJSFrontend -->|Route via Ingress| TraefikGateway
    TraefikGateway --> GrafanaPortal
    TraefikGateway --> TempoTracing
    TraefikGateway --> OtelCollector

    OtelCollector -->|Export Spans| TempoTracing
    GrafanaPortal -->|Query Spans| ClickHouse
    GrafanaPortal -->|Query Traces| TempoTracing
```

---

## 2. Three-Plane Architectural Topology (Control, Data, Messaging)

```mermaid
flowchart TD
    subgraph ControlPlaneArch["1. CONTROL PLANE"]
        EnvConfig["Root Environment Matrix (.env.example)"]
        DockerBridge["Shared Container Network (llmobs-network)"]
        TraefikMiddleware["Traefik Security Headers & Dynamic Router (dynamic.yml)"]
    end

    subgraph DataPlaneArch["2. DATA PLANE"]
        FastApiServer["instrumentation-sdk Ingestion Engine"]
        AlloyDatabase[("Google AlloyDB Omni 15 Transactional Store")]
        ClickHouseDB[("ClickHouse Columnar Telemetry Engine")]
        RedisStore[("Redis Micro-USD Spend Ledger")]

        FastApiServer --> ClickHouseDB
        FastApiServer --> RedisStore
    end

    subgraph MessagingPlaneArch["3. MESSAGING & TELEMETRY PLANE"]
        KafkaBus["Apache Kafka KRaft Message Bus (llmobs-kafka:9092)"]
        OtelPipeline["OpenTelemetry Collector & Tempo Engine (llmobs-otel-collector)"]
        TemporalSagas["Temporal Durable Workflow Framework (llmobs-temporal:7233)"]
        WorkerPool["Asynchronous Worker Consumer Groups"]

        FastApiServer --> KafkaBus
        KafkaBus --> WorkerPool
        WorkerPool --> TemporalSagas
        OtelPipeline --> TempoTracing
    end

    ControlPlaneArch --> DataPlaneArch
    MessagingPlaneArch --> DataPlaneArch
```

---

## 3. Low-Level Design (LLD) Component Specifications

### 1. Ingress Router & Gateway (`llmobs-traefik`)
- **Technology**: Traefik Proxy v3.7
- **Host Bindings**: `31410:80` (HTTP), `31411:8080` (Dashboard API), `31419:443` (HTTPS)
- **Routing Rules**:
  - `llmobs.grafana` -> `llmobs-grafana:3000`
  - `llmobs.tempo` -> `llmobs-tempo:3200`
  - `llmobs.otel` -> `llmobs-otel-collector:4318`
- **Security Middlewares**: IP rate-limiting, CORS origin filtering, payload size limits (`50MB`).

### 2. High-Speed Cache & Spend Ledger (`llmobs-redis`)
- **Technology**: Redis 7 Alpine
- **Host Binding**: `31413:6379`
- **Key Schemas**:
  - `org:{org_id}:spend_micro_usd` -> Hash (`model_name` -> `accrued_micro_usd`)
  - `rate_limit:{tenant_id}:sliding_window` -> Sorted Set (`timestamp` -> `request_id`)
  - `api_key:{key_hash}:ttl_cache` -> Serialized permissions JSON (TTL 300s)

### 3. Event Streaming Bus (`llmobs-kafka`)
- **Technology**: Apache Kafka Latest (KRaft Mode, No Zookeeper)
- **Host Binding**: `31414:9092`
- **Advertised Listeners**: `PLAINTEXT://localhost:31414,PLAINTEXT_INTERNAL://llmobs-kafka:9092`
- **Topic Schemas**:
  - `llm.spans.raw` (3 partitions, 7-day retention)
  - `llm.evaluations.queue` (3 partitions, 48-hour retention)
  - `llm.alerts.triggered` (1 partition, 72-hour retention)
  - `llm.spans.dlq` (1 partition, dead-letter queue)

### 4. Columnar Analytics Database (`llmobs-clickhouse`)
- **Technology**: ClickHouse 24.8 Alpine
- **Host Bindings**: `8123:8123` (HTTP Query API), `9000:9000` (Native TCP)
- **Primary Database**: `llm_telemetry_analytics`
- **Columnar Tables**:
  - `spans_raw` (Engine: `MergeTree`, Partition By `toYYYYMM(timestamp)`, Order By `(org_id, timestamp, span_id)`)
  - `token_aggregates_hourly` (Engine: `SummingMergeTree`, Order By `(org_id, model, toStartOfHour(timestamp))`)

### 5. Relational Transactional Database (`llmobs-alloydb`)
- **Technology**: Google Cloud AlloyDB Omni (`google/alloydbomni:15`)
- **Host Binding**: `31420:5432`
- **Primary Database**: `llm_observability`
- **Relational Tables**: `organizations`, `tenants`, `api_keys`, `prompt_templates`, `evaluations`.

### 6. Distributed Tracing Pipeline (`llmobs-otel-collector` & `llmobs-tempo`)
- **OTEL Collector**: Listens on `4317` (gRPC) & `4318` (HTTP). Processors: `memory_limiter` -> `attributes` -> `resource` -> `batch`.
- **Tempo Store**: Storage and query engine for trace waterfalls listening on `3200` (HTTP) & `4317` (gRPC).

### 7. Workflow & Durable Execution Engine (`llmobs-temporal`)
- **Technology**: Temporal Server `1.24.2` (`auto-setup`)
- **Host Bindings**: `7233:7233` (Engine gRPC), `8088:8080` (Temporal UI)
- **Persistence Driver**: `DB=postgres12` connecting to `llmobs-alloydb:5432`.

### 8. Analytics Portal & Visualizer (`llmobs-grafana`)
- **Technology**: Grafana Latest
- **Host Binding**: `31415:3000`
- **Datasources**: Tempo (`isDefault: true`), ClickHouse (`http://llmobs-clickhouse:8123`).

---

## 4. Complete Environment Variables Matrix (`.env.example`)

| Variable Name | Default Value | Description | Connected Service |
|---|---|---|---|
| `PORT_TRAEFIK_HTTP` | `31410` | Traefik HTTP Ingress Entrypoint | `llmobs-traefik` |
| `PORT_TRAEFIK_DASHBOARD` | `31411` | Traefik Web UI Dashboard | `llmobs-traefik` |
| `PORT_TRAEFIK_HTTPS` | `31419` | Traefik HTTPS Entrypoint | `llmobs-traefik` |
| `PORT_REDIS` | `31413` | Redis In-Memory Cache Port | `llmobs-redis` |
| `REDIS_PASSWORD` | `llmobs_redis_s3cret_2024` | Redis Authentication Secret | `llmobs-redis` |
| `PORT_KAFKA` | `31414` | Kafka KRaft Broker Port | `llmobs-kafka` |
| `PORT_CLICKHOUSE_HTTP` | `8123` | ClickHouse HTTP Query Port | `llmobs-clickhouse` |
| `PORT_CLICKHOUSE_NATIVE` | `9000` | ClickHouse Native Protocol Port | `llmobs-clickhouse` |
| `CLICKHOUSE_DB` | `llm_telemetry_analytics` | ClickHouse Primary Database Name | `llmobs-clickhouse` |
| `PORT_TEMPO` | `31416` | Tempo Trace HTTP Port | `llmobs-tempo` |
| `PORT_OTEL_HTTP` | `31417` | OpenTelemetry OTLP/HTTP Port | `llmobs-otel-collector` |
| `PORT_OTEL_GRPC` | `31418` | OpenTelemetry OTLP/gRPC Port | `llmobs-otel-collector` |
| `PORT_GRAFANA` | `31415` | Grafana Web Portal Port | `llmobs-grafana` |
| `PORT_ALLOYDB` | `31420` | AlloyDB Omni PostgreSQL Port | `llmobs-alloydb` |
| `ALLOYDB_USER` | `admin` | AlloyDB Omni Superuser | `llmobs-alloydb` |
| `ALLOYDB_PASSWORD` | `password` | AlloyDB Omni User Password | `llmobs-alloydb` |
| `ALLOYDB_DB` | `llm_observability` | Primary Transactional Database | `llmobs-alloydb` |
| `PORT_TEMPORAL_UI` | `8088` | Temporal Workflow Admin UI | `llmobs-temporal` |

---

## 5. Security Controls & Pending Security TODO List

### A. Implemented Security Controls (`COMPLETED`)
- [x] **Network Isolation**: All containers communicate exclusively through dedicated bridge `llmobs-network`.
- [x] **Database Isolation**: Decoupled `Database-per-Service` schema pattern across microservices.
- [x] **Docker Socket Hardening**: Traefik mounts `/var/run/docker.sock:ro` strictly read-only.
- [x] **No Plaintext Passwords in Compose**: All secrets parameterized via `.env.example` defaults.
- [x] **Memory Bounding & OOM Guardrails**: Hard memory limits configured on OTEL Collector (`512MB` limit) and ClickHouse.
- [x] **Ingress Security Middleware**: Traefik enforces HTTP security headers (`X-Frame-Options`, `HSTS`, `X-Content-Type-Options`) and rate limiting.

### B. Pending Security TODO List (`NEXT ITERATIONS`)
- [ ] **SEC-01: Inter-Container mTLS Encryption**: Implement TLS mutual authentication on internal OTLP gRPC ports (`4317`) between microservices, OTEL Collector, and Tempo.
- [ ] **SEC-02: External Secrets Management Integration**: Migrate plain-text `.env` credential files to HashiCorp Vault or AWS Secrets Manager sidecar injectors.
- [ ] **SEC-03: Strict Non-Root Container Execution**: Add explicit `user: "1000:1000"` non-root security context across all Docker Compose service definitions.
- [ ] **SEC-04: Web Application Firewall (WAF) Payload Inspection**: Deploy OWASP ModSecurity / Coraza WAF plugin on Traefik to sanitize incoming API payloads for SQL injection and LLM prompt injection.
- [ ] **SEC-05: Central Audit Trail Logging (`pgaudit`)**: Enable `pgaudit` extension on AlloyDB Omni to stream DDL/DML audit events into ClickHouse security analytics table.
- [ ] **SEC-06: CI/CD OCI Container Vulnerability Scanning**: Integrate Trivy automated container image scanning into `.github/workflows/ci.yml` pipeline.

---

## 6. Verification Test Results Matrix

```text
=== STARTING CENTRAL INFRASTRUCTURE VERIFICATION TESTS ===

✅ [Traefik Gateway] HTTP GET http://localhost:31411/api/version -> Status 200 (Active)
✅ [Redis Ledger] TCP Connect localhost:31413 -> SUCCESS (Authenticating)
✅ [Kafka Broker] TCP Connect localhost:31414 -> SUCCESS (KRaft Listening)
✅ [ClickHouse Analytics] HTTP GET http://localhost:8123/ping -> Status 200 (Ok.)
✅ [Tempo Tracing] HTTP GET http://localhost:31416/ready -> Status 200 (ready)
✅ [OTEL Collector gRPC] TCP Connect localhost:31418 -> SUCCESS (Listening)
✅ [Grafana Portal] HTTP GET http://localhost:31415/api/health -> Status 200 (database ok)
✅ [AlloyDB Omni DB] TCP Connect localhost:31420 -> SUCCESS (Engine Ready)
✅ [Temporal Engine] TCP Connect localhost:7233 -> SUCCESS (gRPC Active)

=== ALL 9 CENTRAL INFRASTRUCTURE SERVICES 100% HEALTHY ===
```
