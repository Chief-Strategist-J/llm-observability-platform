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

### Good Latency Metrics Selection
The table below specifies what makes a metric "good" and its critical utility in observability:

| Metric Name | What makes it a Good Metric | Why it is Good / Value | Example Target |
| :--- | :--- | :--- | :--- |
| **Tail Latency (p95/p99)** | Measures the performance of worst-case requests. | Captures degradation seen by heavy users; averages (p50) hide tail spikes. | `p99_total_ms` <= 1500ms |
| **SLO Burn Rate** | A leading indicator showing the rate of error budget consumption. | Alerts operations of a degradation early before the monthly SLA is violated. | `burn_rate_1h` > 14.4x |
| **Time to First Token (TTFT)** | Measures responsiveness in streaming completions. | Directly affects user perceived latency in interactive applications. | `p95_ttft_ms` <= 300ms |
| **Throughput Per Output Token (TPOT)** | Measures LLM execution efficiency independent of completion size. | Decouples document size from processing speed to evaluate true LLM performance. | `tpot_ms` = (total - ttft) / tokens |

### Critical Telemetry & Architectural Tradeoffs
The table below details the design tradeoffs evaluated during the implementation:

| Tradeoff Dimension | Option A (Chosen: Threaded Async Engine) | Option B (Alternative: Isolated Process) | Tradeoff Rationale |
| :--- | :--- | :--- | :--- |
| **Query Latency vs. CPU Contention** | Low query latency due to shared-memory cache retrieval. May cause minor CPU context-switch overhead under high request throughput. | Zero CPU impact on the ingestion worker. Higher deployment costs and slight I/O network latency. | Threaded model was chosen to prioritize low infrastructure footprint and local cache reads. |
| **High Accuracy vs. Storage Size** | DDSketch relative accuracy set to 1% (`relative_accuracy=0.01`). | Raw transaction telemetry storage in ClickHouse/S3. | Storing raw spans is cost-prohibitive. DDSketches capture precise tail percentiles with a constant, small memory footprint. |
| **Immediate Consistency vs. Resource Overhead** | Pipeline batch writes (`pipe.execute()`) reduce network overhead. | Eventual consistency in metric queries (1-minute latency lag). | We compromise minor query consistency to avoid overwhelming Redis with single-key writes. |

## Decision Hierarchy Tree
Below is the structural decision path followed for this API design choice:

```
Implement Latency Engine REST Query API
│
├── Functional Requirements
│   ├── Query Latency Percentiles (p50, p95, p99)
│   ├── Query SLO Burn Rates (1h, 6h, 3d windows)
│   ├── Query Historical Baselines (past N days)
│   └── Service-to-Service HS256 JWT Authentication
│
├── Non-functional Requirements
│   ├── Low read latency (under 10ms target)
│   ├── High ingestion availability (non-blocking thread model)
│   └── Conformity with OpenAPI v1 specification
│
├── Processing & Threading
│   ├── Option B: Isolated Process
│   └── Option A: Threaded Async FastAPI ✓
│       └── Reason:
│           ├── Reuses port 8002 footprint
│           └── Non-blocking polling loop concurrency
│
├── Ingestion Storage (Cache)
│   ├── Memcached
│   └── Redis ✓
│       └── Reason:
│           ├── Fast raw DDSketch merges
│           ├── Multi-window SLO bucket pipelining
│           └── Automatic TTL management
│
├── Long-term Storage (Baseline)
│   ├── PostgreSQL
│   └── ClickHouse ✓
│       └── Reason:
│           ├── Multi-million metrics column storage
│           ├── Fast daily p99 aggregations
│           └── Lazy-connection test isolation
│
└── Deployment
    ├── Docker Container (FastAPI + Kafka Consumer thread)
    ├── Redis Instance
    └── ClickHouse Cluster
```

## Architectural Mental Models

### 1. Failure-First Model
Enumerate and design for system failures prior to designing the happy execution paths:
* **Lazy DB Connection**: The ClickHouse adapter delays client instantiation until query-time (`@property`). This prevents eager connection attempts from failing HTTP server startup or breaking unit tests when ClickHouse is offline.
* **Non-Blocking Telemetry Ingestion**: The query service runs in a daemon background thread. If query load spikes or blocks, the worker's Kafka consumer loop continues polling and committing offsets without dropping events.
* **Configurable Port Fail-Safe**: Avoids hard-coded port bindings. The server port defaults to `8002` but is configurable via `HEALTH_PORT` to prevent startup collisions.

### 2. Ports and Adapters (Hexagonal Architecture)
Maintain strict separation of business logic from framework and platform side-effects:
* **Pure Core Logic**: `LatencyQueryService` is framework-agnostic. It contains zero imports of FastAPI or raw Redis/ClickHouse drivers, executing entirely through interface protocols.
* **Swappable Infrastructure**: Adapters (`LatencyRedisAdapter`, `LatencyClickHouseAdapter`) implement the defined ports (`LatencyRedisPort`, `LatencyClickHousePort`) structurally, meaning databases or drivers can be replaced with zero impact to the service layer.

### 3. Logarithmic Percentile Compression (DDSketch)
Optimize memory consumption while maintaining high percentile resolution:
* **Sketch Storage**: Rather than storing raw timestamps (which grow linearly with traffic), we persist compressed logarithmic sketches in Redis.
* **Low Relative Error**: Restricts percentiles error bounds to 1% (`relative_accuracy=0.01`), ensuring that tail latency metrics (p95/p99) remain highly accurate with constant-size cache keys.

## Relationship & Synergy: Using DDSketches and SLOs Together
In latency observability, DDSketches and SLO trackers are complementary mechanisms. We use both together to create a complete detection and diagnostics workflow:

1. **SLOs act as the Leading Indicator (Alerting Boundary)**:
   * **Role**: SLO tracking answers the question: *"Are our clients currently experiencing acceptable service performance?"*
   * **Mechanism**: By comparing incoming spans against a threshold, the SLO tracker computes rolling error budgets. If a spike in latency consumes the budget, it triggers alerts (e.g. high 1-hour burn-rate).
   
2. **DDSketches act as the Diagnostic Tool (Bottleneck Identification)**:
   * **Role**: DDSketches answer the question: *"What does the actual latency distribution look like, and how bad is the degradation?"*
   * **Mechanism**: When an SLO alert fires, operators query the DDSketch endpoint (`/v1/latency/percentiles`). The DDSketch percentiles (p50, p95, p99) help diagnose whether the issue is caused by a subset of extremely slow tail-end requests (high p99, flat p50) or a systemic slowdown affecting all requests (both p50 and p99 elevated).

3. **Combined Operational Workflow**:
   * **Detection**: High SLO burn rate alerts operations of a degradation.
   * **Diagnosis**: Operators check `/v1/latency/percentiles` to identify the tail latency magnitude (p95/p99 spikes).
   * **Historical Correlation**: Operators query `/v1/latency/baseline` to compare the current DDSketch percentile profiles against historical ClickHouse baseline metrics to confirm if the regression is a novel event or a recurring daily pattern.

## Failure Modes Created

### FM-1: Port conflicts on port 8002
* **Symptom**: Service fail-starts with port already in use.
* **Detection**: Startup logs contain port binding error.
* **Prevention**: HTTP port is fully configurable via `HEALTH_PORT` environment variable.

## Review Trigger
* Review if HTTP query volume exceeds 10,000 requests/second (at that point, Option B becomes necessary).
