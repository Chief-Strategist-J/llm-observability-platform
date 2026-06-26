# ADR-011: Implement FastAPI service-to-service REST Query API for latency-engine

* **Status**: Accepted
* **Date**: 2026-06-26
* **Deciders**: Jaydeep

## Context and Problem Statement
How can upstream systems and observability dashboards query calculated percentiles, SLO burn rates, and historical baselines from latency-engine securely and performantly?

## Decision Drivers
* **D1**: Access to metrics must be secured via service-to-service authentication.
* **D2**: Telemetry query processing must not block worker's CPU-bound Kafka polling loop.
* **D3**: API responses must strictly conform to the OpenAPI v1 contract specs.
* **D4**: ClickHouse connection outages must not prevent HTTP server startup.

## Business Decision Tree (Ingestion & Processing Flow)
The latency engine evaluates every consumed span against the following processing paths to ensure correct stats aggregation:

```
                          [Raw Span Event Consumed]
                                      │
                                      ▼
               [Validate Span: Has model & latency_ms_total?]
                               /             \
                       (No)   /               \   (Yes)
                             ▼                 ▼
                     [Skip Span]       [Parse UTC Timestamp]
                                               │
           ┌───────────────────────────────────┼──────────────────────────────────┐
           │                                   │                                  │
           ▼                                   ▼                                  ▼
[latency_ms_ttft exists?]             [Is retry_count > 0?]             [SLO threshold check]
      /         \                           /         \                       /         \
(No) /           \ (Yes)             (Yes) /           \ (No)           (Yes)/           \(No)
    ▼             ▼                       ▼             ▼                   ▼             ▼
[Skip]     [Update TTFT Sketch]     [Update Retry]  [Update Total]     [Incr Errors    [Incr Total
           (sketch:ttft:{m}:{h})     (sketch:retry)  (sketch:total)     & Total]        Only]
                  │                                                         │               │
                  ▼                                                         ▼               ▼
           [TPOT Eligible?]                                                 └───────┬───────┘
         (TTFT & Tokens > 0,                                                        │
          Reason != timeout)                                                        │
              /         \                                                           ▼
      (No)   /           \ (Yes)                                           [Attribution tags?]
            ▼             ▼                                                    /          \
         [Skip]     [Calc TPOT]                                         (Yes) /            \ (No)
                    (tpot:latest)                                            ▼              ▼
                                                                     [Store Hash    [Skip]
                                                                      & Agg Avg]
```

### Why this is Critical & Important:
* **Tail Latency Accuracy (p95/p99)**: Capturing tail latencies in LLM interactions is vital because typical average (p50) values hide severe bottlenecks. Using DDSketches allows the system to aggregate raw logs into memory-efficient, mathematically accurate percentiles dynamically.
* **Non-Blocking Query Separation**: If HTTP query requests block the consumer worker's CPU-bound Kafka poller, offsets will lag, creating database backpressure and telemetry delay. Running the query API on a background thread preserves consumer throughput under heavy traffic spikes.
* **SLO Error Budgeting**: Accurate tracking of SLO burn rates (over 1h, 6h, and 3-day windows) triggers leading indicators of platform degradation. The query API surfaces these budgets securely via service-to-service JWT to allow automatic remediation before client SLA breaches occur.

## Options Considered
* **Option A**: FastAPI app running on a background thread within the consumer process.
* **Option B**: Independent query service deployment.

## Pros and Cons of Options

### Option A: FastAPI app running on a background thread within the consumer process
* **Good**: Reuses existing exposed HTTP port (`8002`), doesn't block the Kafka consumer loop because it runs in a separate thread.
* **Good**: Leverages FastAPI for parameter validation, dependency injection, and JWT verification.
* **Bad**: CPU resource contention if request rates scale past limits.

### Option B: Independent query service deployment
* **Good**: Complete process isolation between consumer loop and API readers.
* **Bad**: Increases container deployment footprint, requires additional network management and configuration.

## Decision Outcome
**Chosen**: Option A (FastAPI app running via uvicorn in a daemon thread).
* **Rationale**: Reuses the existing port setup, keeps the deployment footprint lightweight, and meets all performance, security, and contract constraints.

## Failure Modes Created

### FM-1: Port conflicts on port 8002
* **Symptom**: Service fail-starts with port already in use.
* **Detection**: Startup logs contain port binding error.
* **Prevention**: HTTP port is fully configurable via `HEALTH_PORT` environment variable.

## Review Trigger
* Review if HTTP query volume exceeds 10,000 requests/second (at that point, Option B becomes necessary).
