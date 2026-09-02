# ADR-0009: Dynamic Service Registry, Discovery & Client-Side Load Balancing

| Field | Value |
|---|---|
| Document ID | ADR-0009 |
| Status | Accepted |
| Author(s) | Architecture Steering Committee |
| Target Package | `packages/configs/llm-obs-infra/service-discovery` |
| Date | 2026-09-02 |

---

## Context

All inter-service communication within the LLM Observability Platform relies on hardcoded static endpoints and port numbers across Python microservices (`latency-engine`, `event-cost`, `quality-engine`), Node.js applications (`web-app`, `auth`), and Go services (`ai-service`). This introduces three critical failure vectors:

1. **Brittle Endpoint Coupling**: When a service port changes, a container restarts on a different IP, or a host is reconfigured, static endpoint references silently break with no diagnostic feedback.
2. **Zero Health Visibility**: Callers have no way to know whether a target service is alive, degraded, or dead before sending requests. Failed requests return opaque network errors with no actionable root-cause context.
3. **No Automatic Failover**: When one instance of a service goes down, traffic continues to flow to the dead endpoint. There is no mechanism for routing to healthy replicas, retrying against alternative nodes, or circuit-breaking persistently failing targets.

---

## Decision

Implement a **Dynamic Service Registry** written in Go, deployed as a containerized sidecar within the existing `llm-obs-infra` Docker Compose stack, providing:

### Phase 1 — Core Registry Engine
- **Dynamic Runtime Registration**: Services register by logical name (e.g. `"ai-service"`, `"clickhouse"`) at startup via HTTP REST API. Endpoints are never hardcoded in application code.
- **Heartbeat Lease Manager**: Background daemon sweeping registered instances every 3 seconds. Instances missing heartbeats beyond a 15-second TTL are marked `UNHEALTHY`; instances exceeding 60-second eviction TTL are removed entirely.
- **Active Health Prober**: Data-driven probe strategies (HTTP `GET /health` and TCP `net.Dial`) registered in an extensible strategy map. New probe protocols can be added by registering a single function — no core logic modification required.
- **Client-Side Load Balancing**: Five algorithms (Round Robin, Weighted Round Robin, Least Connections, Power of Two Choices, Consistent Hash) registered as factories in a data-driven map. The active algorithm is selected via `config.json`.
- **Circuit Breaker**: Per-instance state machine (`CLOSED` → `OPEN` → `HALF_OPEN` → `CLOSED`) with data-driven thresholds and cooldown durations.
- **Seed Service Catalog**: Pre-populated `services.json` file containing all 9 infrastructure services from `docker-compose.yml`, so the registry is immediately useful without application changes.

### Phase 2 — Traefik Dynamic Provider Integration
- **Topology Exporter**: Subscribes to registry change events and regenerates `config/traefik/dynamic/discovery.yml` containing only verified healthy instances.
- **Auto-Reload**: Traefik's existing `watch: true` file provider setting automatically reloads the generated config, enabling clean domain-based routing (e.g. `http://ai-service.llmobs.local`).

### Cross-Language Access
- The registry exposes an HTTP REST + Server-Sent Events (SSE) gateway on port `31426`. Language-specific client SDKs (Python, Node.js, Go) are implemented at the individual service level — not bundled in this package — to maintain single-responsibility boundaries.

---

## Architecture

```
Application Services (Python / Node / Go)
    │
    │  HTTP REST API (:31426)
    ▼
┌─────────────────────────────────────────────────┐
│  Go Service Registry Engine                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Registry │  │ Lease    │  │ Health       │  │
│  │ (Memory) │  │ Manager  │  │ Prober       │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│  ┌──────────┐  ┌──────────┐                     │
│  │ Load     │  │ Circuit  │                     │
│  │ Balancer │  │ Breaker  │                     │
│  └──────────┘  └──────────┘                     │
│  ┌──────────────────────────────────────────┐   │
│  │ Traefik Dynamic Provider Exporter        │   │
│  │ → writes discovery.yml on topology change│   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
    │
    │  Traefik auto-reloads (watch: true)
    ▼
┌─────────────────────────────────────────────────┐
│  Traefik v3.7 Ingress Gateway                   │
│  ai-service.llmobs.local → healthy endpoint     │
│  clickhouse.llmobs.local → healthy endpoint     │
└─────────────────────────────────────────────────┘
```

---

## Data-Driven Design Principles Applied

| Principle | Implementation |
|---|---|
| Probe strategies as data | `probeStrategies` map keyed by protocol string. New protocols added via `RegisterProbeStrategy()`. |
| LB algorithms as data | `balancerFactories` map keyed by algorithm string. New algorithms added via `RegisterAlgorithm()`. |
| Status/event names as data | Lookup maps (`healthStatusNames`, `eventTypeNames`) instead of switch statements. |
| Config-driven behavior | All thresholds, intervals, TTLs, and algorithm selection controlled by `config.json`. |
| Seed catalog as data | Infrastructure services defined in `services.json`, loaded at startup. |

---

## Consequences

### Positive
- Eliminates all hardcoded endpoint references across the polyglot service fleet.
- Provides instant failure diagnostics when services go down, including per-instance probe error details.
- Enables automatic failover to healthy replicas via client-side load balancing.
- Integrates with existing Traefik gateway for clean domain-based routing without additional infrastructure.
- Zero external dependencies (no Consul, etcd, or Kubernetes required for local development).

### Negative
- Adds one additional container (`llmobs-service-registry`) to the Docker Compose stack.
- In-memory registry state is lost on container restart (mitigated by seed catalog auto-reload and fast re-registration).
- Application services must implement a heartbeat loop to remain registered (simple HTTP POST every 5 seconds).

### Risks
- **Single Point of Failure**: The registry itself is a single-instance service. Mitigated by: (a) seed catalog ensures known infrastructure services are always available, (b) Traefik continues serving last-known-good `discovery.yml` if the registry goes down.

---

## Related Documents

- [Infrastructure Specification & Architecture Reference](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/README.md)
- [Docker Compose Stack](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docker-compose.yml)
- [Traefik Dynamic Configuration](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/config/traefik/dynamic.yml)
