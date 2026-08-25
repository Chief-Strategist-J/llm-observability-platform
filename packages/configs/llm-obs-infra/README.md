# Centralized Platform Infrastructure (`llm-obs-infra`)

This package (`packages/configs/llm-obs-infra`) serves as the single source of truth for the entire platform's shared infrastructure stack.

---

## 🏗️ Architecture & Core Platform Services (`llmobs-*`)

All platform services (Python, Node, Go, Rust, Java, Dart, Swift, Kotlin) connect to the central `llmobs-network` Docker bridge network orchestrating these `llmobs-*` services:

| Component Service | Container Name | Host Port Binding | Internal Endpoint | Core Service Purpose |
|---|---|---|---|---|
| **`llmobs-traefik`** | `llmobs-traefik-gateway` | `31410` (HTTP)<br>`31411` (Dashboard)<br>`31419` (HTTPS) | `http://llmobs-traefik:80` | Reverse proxy, SSL termination & rate limiting |
| **`llmobs-redis`** | `llmobs-redis-ledger` | `31413` | `llmobs-redis:6379` | Spend ledgers, API key TTL cache & atomic counters |
| **`llmobs-kafka`** | `llmobs-kafka-broker` | `31414` | `llmobs-kafka:9092` | Primary Apache Kafka event stream bus (`llm.spans.raw`) |
| **`llmobs-redpanda`** | `llmobs-redpanda-broker` | `31422` | `llmobs-redpanda:9092` | High-throughput Redpanda stream broker alternative |
| **`llmobs-clickhouse`** | `llmobs-clickhouse-analytics` | `8123` (HTTP)<br>`9000` (Native) | `http://llmobs-clickhouse:8123` | Columnar telemetry & span analytics engine |
| **`llmobs-grafana`** | `llmobs-grafana-portal` | `31415` | `http://llmobs-grafana:3000` | Operational telemetry dashboards |
| **`llmobs-tempo`** | `llmobs-tempo-tracing` | `31416` | `http://llmobs-tempo:3200` | Distributed trace waterfall storage & query engine |
| **`llmobs-otel-collector`** | `llmobs-otel-collector` | `31417` (HTTP)<br>`31418` (gRPC) | `http://llmobs-otel-collector:4318` | OpenTelemetry OTLP trace & metric receiver |
| **`llmobs-alloydb`** | `llmobs-alloydb-db` | `31420` | `llmobs-alloydb:5432` | Partitioned span relational database (AlloyDB Omni) |
| **`llmobs-temporal`** | `llmobs-temporal-engine` | `7233` (gRPC)<br>`8088` (UI) | `llmobs-temporal:7233` | Durable workflow orchestration engine & UI portal |

---

## 🚀 Launch Instructions

To launch the central shared platform infrastructure stack:

```bash
cd packages/configs/llm-obs-infra
docker compose up -d
```
