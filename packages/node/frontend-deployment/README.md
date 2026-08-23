# `@observability/frontend-deployment`

Unified deployment, observability & security package for the LLMObs Platform. Provides Traefik API Gateway with TLS termination, request-level security (rate limiting, payload limits, circuit breaker), Redis cache with authentication, Kafka messaging, and OpenTelemetry trace visualization via Grafana & Tempo.

---

## 🌐 Custom Gateway Domain Links & Service Access Matrix

All web services are fronted by **Traefik API Gateway** with TLS termination on `:31419`.

| Service | Custom Gateway URL | Port | Auth Type | Username / Password |
| :--- | :--- | :--- | :--- | :--- |
| **Grafana UI Dashboard** | [https://llmobs.grafana:31419](https://llmobs.grafana:31419) | `31419` / `31415` | Basic Auth | `admin` / `llmobs_grafana_s3cret_2024` |
| **API Gateway Dashboard** | [https://llmobs.gateway:31419](https://llmobs.gateway:31419) | `31419` / `31411` | Insecure (Dev) | None (Admin Dashboard) |
| **Grafana Tempo (Traces)** | [https://llmobs.tempo:31419](https://llmobs.tempo:31419) | `31419` / `31416` | Network Isolated | None (Internal API) |
| **OTel Collector (Ingest)** | [https://llmobs.otel:31419](https://llmobs.otel:31419) | `31419` / `31417` | Ingestion | None (OTLP Ingestion) |
| **Auth Microservice** | [https://llmobs.gateway:31419/api/v1/auth](https://llmobs.gateway:31419/api/v1/auth) | `31419` | Bearer JWT | Application Tokens |
| **Redis Cache** | `llmobs.redis:31413` | `31413` | Password (`requirepass`) | `llmobs_redis_s3cret_2024` |
| **Kafka Event Broker** | `llmobs.kafka:31414` | `31414` | Plaintext | None |

> 💡 **Required 1-Line Setup for Custom Domains (`llmobs.*`):**
> Run this command once in your terminal to enable DNS resolution for all custom domain URLs:
> ```bash
> echo "127.0.0.1  llmobs.gateway llmobs.grafana llmobs.tempo llmobs.otel llmobs.kafka llmobs.redis" | sudo tee -a /etc/hosts
> ```

---

## 🏛 High-Level System Architecture (HLD)

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer (External Access)"]
        Browser["Browser / Next.js Web App (:31400)"]
        SDK["Observability SDK / API Client"]
    end

    subgraph SecurityGateway["Traefik API Gateway Layer (Host Ports 31410 / 31419)"]
        TLS["TLS 1.2/1.3 Termination (Self-Signed Root CA)"]
        Middlewares["Security Middlewares (Rate Limit, Payload Limit, Headers, Circuit Breaker)"]
        Router["Traefik Dynamic Router (dynamic.yml)"]
    end

    subgraph NetworkBoundary["Isolated Container Network (llmobs-network)"]
        direction TB
        
        subgraph StorageLayer["Data & Messaging Store"]
            Redis["Redis 7 Cache (Password Auth / Cmd Renamed :6379)"]
            Kafka["Kafka Broker (Event Streaming Queue :9092)"]
        end

        subgraph TelemetryPipeline["Observability & Tracing Engine"]
            OTel["OTel Collector Contrib (Metadata Enrichment :4318/:4317)"]
            Tempo["Grafana Tempo (Local WAL / Trace Block Engine :3200)"]
            Grafana["Grafana 10 Dashboard (Tempo Datasource :3000)"]
        end
    end

    %% Client Interactions
    Browser -->|HTTPS :31419| TLS
    SDK -->|OTLP HTTPS :31419| TLS
    TLS --> Middlewares --> Router

    %% Gateway Routing inside Isolated Network
    Router -->|llmobs.grafana| Grafana
    Router -->|llmobs.tempo| Tempo
    Router -->|llmobs.otel| OTel
    Router -->|llmobs.redis| Redis

    %% Telemetry & Storage Inter-container Communications
    OTel -->|OTLP gRPC| Tempo
    Grafana -->|Query Traces| Tempo
    SDK -.->|Session Cache| Redis
    SDK -.->|Event Streaming| Kafka
```

---

## 🔬 Low-Level System Design (LLD)

### 1. Network & Request Security Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant Client as External Client / Browser
    participant HTTP as Traefik HTTP Entrypoint (:31410)
    participant HTTPS as Traefik HTTPS Entrypoint (:31419)
    participant TLS as TLS Termination Engine
    participant Middleware as Security Middleware Chain
    participant Service as Target Backend Container

    Note over Client, HTTP: 1. Unencrypted HTTP Access Attempt
    Client->>HTTP: GET http://llmobs.gateway:31410/api
    HTTP-->>Client: HTTP 301 Permanent Redirect (to https://:31419)

    Note over Client, HTTPS: 2. Encrypted HTTPS Handshake & Request Security
    Client->>HTTPS: ClientHello (TLS 1.2/1.3, SNI: llmobs.gateway)
    HTTPS->>TLS: Match SAN Certificate (server.pem)
    TLS-->>Client: ServerHello & TLS Session Established

    Note over HTTPS, Middleware: 3. Security Inspection
    HTTPS->>Middleware: Evaluate Rate Limit (max 100 req/s, burst 200)
    alt Rate Limit Exceeded
        Middleware-->>Client: HTTP 429 Too Many Requests
    else Request Payload Inspection
        HTTPS->>Middleware: Evaluate Payload Size (max 10 MB)
        alt Payload Exceeds Limit
            Middleware-->>Client: HTTP 413 Payload Too Large
        else Request Validation Passed
            Middleware->>Middleware: Inject Security Headers (HSTS, nosniff, SAMEORIGIN, XSS)
            Middleware->>Service: Forward Request over llmobs-network
            Service-->>Client: HTTP Response with Hardened Headers
        end
    end
```

### 2. Distributed Tracing & Telemetry Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant App as Application SDK
    participant Gateway as Traefik Gateway (llmobs.otel:31419)
    participant OTel as OTel Collector Contrib
    participant Tempo as Grafana Tempo Storage
    participant Grafana as Grafana Visualization UI

    Note over App, Gateway: 1. Trace Span Export
    App->>Gateway: POST https://llmobs.otel:31419/v1/traces (OTLP Protobuf/JSON)
    Gateway->>OTel: Forward to otel-service (internal port :4318)

    Note over OTel, Tempo: 2. Attribute Enrichment & Processing
    OTel->>OTel: Memory Limiter Check (512MB limit)
    OTel->>OTel: Inject Metadata (deployment.environment, service.namespace, network.transport)
    OTel->>Tempo: Export Batch over OTLP gRPC (internal port :4317)
    Tempo->>Tempo: Write to WAL (/var/tempo/wal) & Compact Blocks

    Note over Grafana, Tempo: 3. Trace Query & Visualization
    Grafana->>Tempo: Query Trace ID via Datasource API (http://tempo:3200)
    Tempo-->>Grafana: Return Trace Span Tree & Execution Waterfall
    Grafana-->>App: Display Trace Waterfall in UI (admin / admin)
```

### 3. Session Security & Messaging Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant App as Microservice Client
    participant Redis as Redis Cache (llmobs.redis:31413)
    participant Kafka as Kafka Broker (llmobs.kafka:31414)

    Note over App, Redis: 1. Redis Password Authentication & Session Check
    App->>Redis: TCP Connect (localhost:31413)
    App->>Redis: AUTH llmobs_redis_s3cret_2024
    alt Invalid Password
        Redis-->>App: -ERR invalid password
    else Valid Password
        Redis-->>App: +OK
        App->>Redis: GET session:usr_9921
        Redis-->>App: Return Encrypted Session JSON
    end

    Note over App, Kafka: 2. Event Publishing
    App->>Kafka: Produce Event to Topic (llmobs.auth.events :31414)
    Kafka->>Kafka: Persist Event to Partition Log
    Kafka-->>App: ACK Partition Offset
```

---

## 🛡 Security Middleware Reference Matrix

All request security rules are centrally declared in [`config/traefik/dynamic.yml`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/node/frontend-deployment/config/traefik/dynamic.yml):

| Middleware | Description | Limit / Value | Target Service |
| :--- | :--- | :--- | :--- |
| `rate-limit` | Per-IP request throttle | `100 req/s` (burst `200`) | Gateway, Grafana, Tempo |
| `rate-limit-ingest` | High-throughput telemetry throttle | `500 req/s` (burst `1000`) | OTel Collector |
| `payload-limit` | Maximum body size limit | `10 MB` Request/Response | OTel Collector |
| `payload-limit-small` | Strict API body size limit | `1 MB` Request / `5 MB` Response | Auth Microservice |
| `security-headers` | Response header hardening | `HSTS`, `nosniff`, `SAMEORIGIN`, `XSS` | All Gateway Routes |
| `circuit-breaker` | Automatic fault isolation | `>50%` Error Ratio → `30s` Trip | Auth Microservice |
| `retry-middleware` | Automatic retry on transient failure | `3 Attempts` (100ms backoff) | Auth Microservice |

---

## 📊 Port Allocation Matrix

| Port | Protocol | Service | Host Access | Security Enforcement |
| :--- | :--- | :--- | :--- | :--- |
| `31410` | HTTP | Traefik HTTP Gateway | Exposed | 301 Redirect to HTTPS `:31419` |
| `31411` | HTTP | Traefik Web Dashboard | Exposed | Insecure mode for local dev |
| `31413` | TCP | Redis Cache | Exposed | `requirepass` password authentication |
| `31414` | TCP | Kafka Event Broker | Exposed | Isolated bridge network |
| `31415` | HTTP | Grafana UI | Exposed | Admin authentication (`admin` / password) |
| `31416` | HTTP | Grafana Tempo API | Exposed | Network isolated |
| `31417` | HTTP | OTel Collector HTTP | Exposed | Rate & Payload size limited |
| `31418` | gRPC | OTel Collector gRPC | Exposed | Rate & Payload size limited |
| `31419` | HTTPS | Traefik TLS Gateway | Exposed | TLS 1.2/1.3 + SAN Certs + Security Headers |

---

## 🛠 Usage Commands

```bash
# Setup fresh machine (dependencies check, cert generation, /etc/hosts setup)
npm run setup

# Start infrastructure with auto-health diagnostic
npm run up

# Run 30-point container health & security diagnostic
npm run health

# Run TypeScript automated integration test suite (29 tests)
npm run test

# Regenerate TLS certificates
npm run certs

# Restart infrastructure stack
npm run restart

# Stop infrastructure stack
npm run down
```

---

## 📋 Requirements & Verification

See [REQUIREMENTS.md](./REQUIREMENTS.md) for complete hardware, software dependency, and firewall specifications.
