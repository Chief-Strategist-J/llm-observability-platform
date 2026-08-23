# `@observability/frontend-deployment`

Unified deployment & observability package for the Observability Platform providing network routing, messaging queues, event streaming pipelines, and OpenTelemetry trace visualization.

---

## 🏛 High-Level System Architecture (HLD)

The high-level design separates client-facing HTTP/WebSocket traffic from background telemetry ingestion pipelines and event streaming queues.

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        Browser["Browser / Next.js Web App (:31400)"]
        AuthApp["Auth Microservice (:3001)"]
    end

    subgraph GatewayLayer["API Gateway & Reverse Proxy Layer"]
        Traefik["Traefik API Gateway (:31410 / :31411)"]
    end

    subgraph MessagingLayer["Messaging & Event Pipeline Layer"]
        Kafka["Apache Kafka Event Broker (:31414)"]
        Redis["Redis Cache & Session Store (:31413)"]
    end

    subgraph TelemetryPipeline["Observability & Tracing Pipeline"]
        OTel["OpenTelemetry Collector (:31417 HTTP / :31418 gRPC)"]
        Tempo["Grafana Tempo Trace Engine (:31416)"]
        Grafana["Grafana Telemetry Dashboard (:31415)"]
    end

    subgraph ServiceDB["Database Layer"]
        AuthDB[("Auth Service Database (:31412)")]
    end

    %% Client traffic flow
    Browser -->|HTTP/REST| Traefik
    Traefik -->|Route /api/v1/auth| AuthApp
    AuthApp -->|SQL Queries| AuthDB

    %% Event & Session messaging flow
    AuthApp -->|Publish Auth Events| Kafka
    AuthApp -->|Session Cache| Redis

    %% Telemetry pipeline flow
    Browser -->|OTLP Traces| OTel
    AuthApp -->|OTLP Traces| OTel
    OTel -->|Batch Export| Tempo
    Grafana -->|Query Traces| Tempo
```

---

## 🔬 Low-Level System Design (LLD) — Telemetry & Messaging Pipeline

The low-level design details the exact data processing flow for telemetry events and message queue pipeline handling.

```mermaid
sequenceDiagram
    autonumber
    participant App as Next.js / Auth App
    participant OTel as OTel Collector (:31417)
    participant Batch as Batch Processor
    participant Tempo as Grafana Tempo (:31416)
    participant Grafana as Grafana UI (:31415)
    participant Kafka as Kafka Broker (:31414)

    box Observability Ingestion Pipeline
        participant OTel
        participant Batch
        participant Tempo
        participant Grafana
    end

    box Event Streaming Pipeline
        participant Kafka
    end

    %% Telemetry Flow
    Note over App, OTel: 1. OpenTelemetry Trace Generation
    App->>OTel: POST /v1/traces (JSON/Protobuf over OTLP)
    OTel->>Batch: Queue Span in Memory Buffer
    Note over Batch: 2. Batching (1s timeout / 1024 spans)
    Batch->>Tempo: Export Batched Spans over gRPC (:4317)
    Tempo-->>Tempo: Store Chunk & Index in Local WAL

    %% Grafana Query Flow
    Note over Grafana, Tempo: 3. Trace Visualization Query
    Grafana->>Tempo: GET /api/traces/{traceId} (:3200)
    Tempo-->>Grafana: Return Span Waterfall & Metadata

    %% Messaging Event Flow
    Note over App, Kafka: 4. Async Event Streaming
    App->>Kafka: Produce Event to Topic (e.g. user.signed_up)
    Kafka-->>App: ACK (Offset Saved)
```

---

## 🚀 Services & Unique Port Allocation Matrix

To prevent port collisions with system or local development services, all services in this stack use unique dedicated host ports:

| Service | Host Port | Internal Port | Protocol / Description |
| :--- | :--- | :--- | :--- |
| **Traefik API Gateway** | `31410` | `80` | Entrypoint router |
| **Traefik Dashboard** | `31411` | `8080` | Gateway Web UI |
| **Redis** | `31413` | `6379` | Cache & Session Store |
| **Kafka Broker** | `31414` | `9092` | Event Streaming Broker |
| **Grafana UI** | `31415` | `3000` | Telemetry Dashboard (`admin` / `admin`) |
| **Grafana Tempo** | `31416` | `3200` | Trace Backend Store |
| **OTel Collector HTTP** | `31417` | `4318` | OpenTelemetry OTLP HTTP Ingestion |
| **OTel Collector gRPC** | `31418` | `4317` | OpenTelemetry OTLP gRPC Ingestion |

---

## 🛠 Usage Commands

From inside this package (`packages/node/frontend-deployment`):

```bash
# Start all infrastructure containers
npm run up

# Check health and status of containers
npm run status

# View live container logs
npm run logs

# Run integration & health test suite
npm run test

# Free stack ports if needed
npm run free-ports

# Stop all infrastructure containers
npm run down
```
