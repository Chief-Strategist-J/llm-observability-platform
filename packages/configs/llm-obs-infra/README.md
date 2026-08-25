# Centralized Platform Infrastructure (`llm-obs-infra`)

This package (`packages/configs/llm-obs-infra`) serves as the single source of truth for the entire platform's shared infrastructure stack.

---

## 🏗️ Architecture & Core Services (`llmobs-*`)

All platform services (Python, Node, Go, Rust, Java, Dart, Swift, Kotlin) connect to the central `llmobs-network` Docker bridge network orchestrating these `llmobs-*` services:

| Component Service | Container Name | Host Port Binding | Internal Endpoint | Purpose |
|---|---|---|---|---|
| **`llmobs-traefik`** | `llmobs-traefik-gateway` | `31410` (HTTP), `31411` (Dashboard), `31419` (HTTPS) | `http://llmobs-traefik:80` | Reverse proxy & SSL termination |
| **`llmobs-redis`** | `llmobs-redis-ledger` | `31413` | `llmobs-redis:6379` | Micro-USD spend ledgers & TTL cache |
| **`llmobs-kafka`** | `llmobs-kafka-broker` | `31414` | `llmobs-kafka:9092` | Event stream bus (`llm.spans.raw`) |
| **`llmobs-grafana`** | `llmobs-grafana-portal` | `31415` | `http://llmobs-grafana:3000` | Operational telemetry dashboards |
| **`llmobs-tempo`** | `llmobs-tempo-tracing` | `31416` | `http://llmobs-tempo:3200` | Trace waterfall storage & query engine |
| **`llmobs-otel-collector`** | `llmobs-otel-collector` | `31417` (HTTP), `31418` (gRPC) | `http://llmobs-otel-collector:4318` | OpenTelemetry OTLP receiver endpoint |
| **`llmobs-postgres`** | `llmobs-postgres-db` | `31420` | `llmobs-postgres:5432` | Partitioned span relational database |

---

## 🚀 Launch Instructions

To launch the central shared platform infrastructure stack:

```bash
cd packages/configs/llm-obs-infra
docker compose up -d
```
