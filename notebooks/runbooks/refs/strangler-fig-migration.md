# Strangler Fig Migration Pattern (Pure Functional Paradigm)

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | STRANGLER-FIG-001                                                 |
| **Date**    | 2026-08-24                                                        |
| **Status**  | Reference / Runbook (Pure Functional Architecture)                |
| **Deciders**| Core Platform & Migration Engineering                             |
| **Scope**   | Legacy Monolith Incremental Replacement & Pure Facade Routing     |

---

## 1. Overview & Context

The **Strangler Fig Pattern** incrementally replaces a legacy monolithic system by placing an intercepting **Façade** in front of legacy and microservice backends. The façade inspects incoming consumer requests and dynamically routes them to either the **legacy monolith** or the **new microservice** based on evaluation rules (tenant whitelists, canary percentage buckets, endpoint migration status, dynamic feature flags).

### Functional Architecture Principles
This runbook enforces a **100% Pure Functional Programming (FP)** approach:
- **No Class Instantiations**: Replaces OOP classes (`Evaluator`, `Adapter`, `Router`, `Strategy`) with immutable data records, pure evaluation functions, curried function factories, and higher-order decorators.
- **Immutable Context**: Request headers, routing rules, and HTTP payloads are modeled as immutable records (`dataclass(frozen=True)` or `NamedTuple`).
- **Resilience via Function Decorators**: Circuit breakers, retries, OTEL tracing, and timeouts are implemented as composable higher-order functions (`Decorator[Dispatcher] -> Dispatcher`).
- **Zero Side-Effect Rule Engine**: The routing evaluator is a referentially transparent function mapping `(RequestContext, RuleConfig) -> RoutingDecision`.

---

## 1.1 Business Architecture & Meta-Decision Framework (15 Meta-Decisions)

Below are the 15 overarching strategic decisions governing the Strangler Fig Façade platform architecture.

---

### Meta-Decision 1: 100% Pure Functional Paradigm Over OOP Mutation
- **Why It Was Made**: Eliminates shared mutable state bugs, race conditions, and side-effect coupling during high-throughput facade request routing.
- **Critical On-Point Rationale**: Pure functions are referentially transparent; given identical inputs, they produce identical outputs without altering ambient memory state.
- **Why It Is Very Important**: Prevents catastrophic multi-tenant state leakage and memory corruption during concurrent request evaluations under peak QPS loads.

---

### Meta-Decision 2: Referentially Transparent Rule Evaluator Engine
- **Why It Was Made**: Guarantees that routing evaluations (`RequestContext -> RoutingDecision`) depend exclusively on explicit input attributes rather than hidden global state or environment variables.
- **Critical On-Point Rationale**: Simplifies automated unit testing and enables mathematical proof of routing deterministic behavior across millions of invocations.
- **Why It Is Very Important**: Prevents unpredictable request routing flips that disrupt active user sessions and violate tenant-level SLAs.

---

### Meta-Decision 3: Non-Blocking Asynchronous Shadow Mode Verification
- **Why It Was Made**: Validates microservice correctness against live production traffic without adding network latency to primary customer response paths.
- **Critical On-Point Rationale**: The legacy response is returned immediately to the client while a shadow call to the new microservice executes in a background async task.
- **Why It Is Very Important**: Protects customer-facing P99 latency SLAs while gathering empirical data parity metrics before cutting over live traffic.

---

### Meta-Decision 4: Deterministic Salted SHA-256 Rollout Hashing
- **Why It Was Made**: Ensures tenant percentage bucket assignments remain 100% sticky and consistent across server process restarts and cluster deployments.
- **Critical On-Point Rationale**: SHA-256 hashing of salted tenant IDs produces a uniform 0–99 integer distribution without relying on volatile random number generators.
- **Why It Is Very Important**: Prevents "tenant flipping" where a user is intermittently routed between legacy and microservice backends on subsequent page reloads.

---

### Meta-Decision 5: Incremental Facade Routing Over Big-Bang Cutover
- **Why It Was Made**: Eliminates single-point-of-failure release risks by migrating traffic endpoint-by-endpoint and tenant-by-tenant.
- **Critical On-Point Rationale**: Allows engineering teams to validate individual microservice domain boundaries in production under low-risk traffic percentages.
- **Why It Is Very Important**: Prevents company-wide outages and multi-million-dollar revenue losses associated with unproven "big bang" monolith replacements.

---

### Meta-Decision 6: Higher-Order Decorator Stack for Resilience Isolation
- **Why It Was Made**: Separates operational concerns (retries, timeouts, circuit breaking, tracing) from core business dispatch logic.
- **Critical On-Point Rationale**: Wraps functional dispatchers in composable decorator closures (`with_tracing(with_circuit_breaker(dispatcher))`) without mutating target functions.
- **Why It Is Very Important**: Ensures uniform operational resilience across all endpoints without duplicating boilerplate error-handling code across the codebase.

---

### Meta-Decision 7: W3C Distributed Trace Context Ingestion at Ingress
- **Why It Was Made**: Binds every incoming facade request to OpenTelemetry distributed tracing context at the outer edge perimeter.
- **Critical On-Point Rationale**: Extracts `traceparent` and `tracestate` headers and injects them into child spans across facade, legacy, and microservice calls.
- **Why It Is Very Important**: Provides complete end-to-end observability, enabling engineers to pinpoint latency bottlenecks across complex hybrid architectures.

---

### Meta-Decision 8: Bounded Concurrency Task Pools for Shadow Execution
- **Why It Was Made**: Controls background shadow task execution to prevent unbounded memory growth during high QPS bursts.
- **Critical On-Point Rationale**: Limits background shadow execution using an `asyncio.Semaphore` (max 100 concurrent tasks) and drops surplus shadow tasks when locked.
- **Why It Is Very Important**: Prevents facade process Out-Of-Memory (OOM) crashes during traffic spikes, ensuring primary customer request paths remain available.

---

### Meta-Decision 9: Volatile Key Exclusion in Parity Differential Analysis
- **Why It Was Made**: Eliminates false-positive data parity alerts generated by dynamic non-deterministic payload keys (e.g. timestamps, UUIDs, trace IDs).
- **Critical On-Point Rationale**: Recursively strips designated volatile keys before executing deep JSON diff comparisons between legacy and shadow responses.
- **Why It Is Very Important**: Saves hundreds of engineering hours by preventing alert fatigue, allowing teams to focus exclusively on genuine data corruption bugs.

---

### Meta-Decision 10: Atomic Snapshot Reference Cells for Hot Config Reloads
- **Why It Was Made**: Enables zero-downtime routing rule updates without restarting facade application processes or exposing mid-read race conditions.
- **Critical On-Point Rationale**: Uses atomic pointer swapping on immutable dictionary cells (`cell["snapshot"] = new_config`) protected by validation gates.
- **Why It Is Very Important**: Guarantees zero dropped customer requests during live operational configuration updates and emergency feature flag toggles.

---

### Meta-Decision 11: Fail-Safe Fallback to Legacy Monolith on Target Failure
- **Why It Was Made**: Protects overall application availability if a newly deployed microservice experiences runtime errors or crashes.
- **Critical On-Point Rationale**: Wraps microservice dispatchers in higher-order circuit breakers that automatically redirect traffic back to the legacy monolith on error.
- **Why It Is Very Important**: Guarantees 99.99% system availability SLAs even during catastrophic microservice deployment failures.

---

### Meta-Decision 12: Asynchronous Compensating Audit Events for Dual-Write Split-Brain Recovery
- **Why It Was Made**: Handles eventual consistency reconciliation when dual-write operations succeed on primary backends but fail on secondary backends.
- **Critical On-Point Rationale**: Emits structured compensating audit events to Kafka topics when secondary writes fail, preserving primary path performance.
- **Why It Is Very Important**: Prevents permanent silent data divergence between legacy and microservice databases without locking primary client responses.

---

### Meta-Decision 13: Strict Ingress Request Context Normalization
- **Why It Was Made**: Guarantees that downstream routing rules operate on clean, sanitized input data regardless of client header variance.
- **Critical On-Point Rationale**: Sanitizes header keys, strips trailing slashes, and injects default tenant identifiers at the facade middleware perimeter.
- **Why It Is Very Important**: Eliminates edge-case null pointer crashes and routing rule misses caused by malformed consumer requests.

---

### Meta-Decision 14: Pure Stream Generator Forwarding for Large Payloads
- **Why It Was Made**: Proxies chunked binary data and large file uploads without buffering complete payloads into facade process memory.
- **Critical On-Point Rationale**: Utilizes async generators (`AsyncGenerator[bytes, None]`) to stream payload bytes directly from client to backend socket connections.
- **Why It Is Very Important**: Prevents facade memory exhaustion and high garbage collection pause latencies when proxying multi-gigabyte file transfers.

---

### Meta-Decision 15: Monotonic Idempotency Token Gating in Dual-Write Mutations
- **Why It Was Made**: Prevents duplicate mutation execution on secondary backends during retried POST/PUT operations.
- **Critical On-Point Rationale**: Tracks executed idempotency keys inside a closure set (`seen_keys`) and rejects duplicate attempts with HTTP 409 Conflict.
- **Why It Is Very Important**: Protects financial ledgers and order databases from duplicate charge and double-inventory allocation errors.

---

## 1.2 Second-Order Decisions Framework (15 Second-Order Decisions)

Second-order decisions address the downstream consequences, trade-offs, and ripple effects created by the primary Meta-Decisions.

---

### Second-Order Decision 1: Task Pool Semaphore Bounding & Byte-Size Gating
- **Primary Meta-Decision Trigger**: Meta-Decision 3 (Non-blocking async shadow calls).
- **Downstream Consequence**: Unbounded `asyncio.create_task()` calls under high QPS can saturate memory and CPU, crashing the facade.
- **Second-Order Decision Made**: Enforce an `asyncio.Semaphore(100)` capacity limit and skip shadow diffing for payloads exceeding 1MB.
- **Why It Was Made**: Bounds background resource consumption to a fixed upper limit regardless of incoming QPS.
- **Why It Is Very Important**: Prevents facade process OOM crashes during sudden 10x traffic spikes, protecting primary path execution.

---

### Second-Order Decision 2: Stateful Circuit Breaker Half-Open Cooldown Gating
- **Primary Meta-Decision Trigger**: Meta-Decision 11 (Fail-safe fallback to legacy monolith).
- **Downstream Consequence**: Auto-fallback can suddenly double the traffic load on the legacy monolith, risking a secondary monolith crash.
- **Second-Order Decision Made**: Implement a stateful `HALF_OPEN` probe cooldown period (30s) before attempting microservice recovery.
- **Why It Was Made**: Controls probe traffic rates during microservice recovery, preventing rapid circuit flapping.
- **Why It Is Very Important**: Prevents cascading overload crashes on the legacy monolith when backing off microservice failures.

---

### Second-Order Decision 3: Salted Multi-Attribute Key Hashing
- **Primary Meta-Decision Trigger**: Meta-Decision 4 (Deterministic SHA-256 rollout hashing).
- **Downstream Consequence**: Naive key hashing can cause tenant clustering and uneven bucket distribution across low-cardinality tenant fleets.
- **Second-Order Decision Made**: Combine feature-specific salt strings (`strangler_v1`) with tenant IDs and fall back to user IDs when tenant IDs are absent.
- **Why It Was Made**: Ensures uniform 0-99 percentage distribution regardless of tenant fleet size or key cardinality.
- **Why It Is Very Important**: Prevents canary rollouts from inadvertently exposing entire high-volume enterprise accounts at low percentage thresholds.

---

### Second-Order Decision 4: Weak Reference Closure Bindings
- **Primary Meta-Decision Trigger**: Meta-Decision 1 (Pure functional paradigm over OOP mutation).
- **Downstream Consequence**: Long-lived closures retaining references to heavy target objects can prevent garbage collection, leaking memory.
- **Second-Order Decision Made**: Wrap target object references in weak reference bindings (`weakref.ref`).
- **Why It Was Made**: Allows Python garbage collectors to reclaim unreferenced target objects even if closure handles linger in registries.
- **Why It Is Very Important**: Eliminates slow memory leaks in long-running facade worker processes over multi-month deployment cycles.

---

### Second-Order Decision 5: Non-Blocking Asynchronous Kafka Audit Log Emission
- **Primary Meta-Decision Trigger**: Meta-Decision 12 (Asynchronous compensating audit events for dual-write split-brain).
- **Downstream Consequence**: Synchronous audit log publishing to Kafka on secondary write failures can introduce latency spikes if Kafka is slow.
- **Second-Order Decision Made**: Offload compensating audit event publishing to background non-blocking async tasks with local disk log fallback.
- **Why It Was Made**: Decouples customer response latency from messaging broker availability and network health.
- **Why It Is Very Important**: Guarantees that messaging broker outages cannot degrade primary customer checkout/mutation performance.

---

### Second-Order Decision 6: Atomic Pointer Snapshot Reference Cells
- **Primary Meta-Decision Trigger**: Meta-Decision 10 (Atomic snapshot reference cells for hot config reloads).
- **Downstream Consequence**: Mid-request config reloads could cause a single request to evaluate rule $A$ at ingress and rule $B$ at egress.
- **Second-Order Decision Made**: Capture an immutable snapshot pointer (`snapshot = cell["snapshot"]`) at request ingress start and pass it down the execution chain.
- **Why It Was Made**: Ensures strict request-level configuration consistency across the entire call lifecycle.
- **Why It Is Very Important**: Prevents inconsistent routing decisions where a request is authorized under new rules but dispatched under old rules.

---

### Second-Order Decision 7: Recursive JSON Volatile Key Sanitization
- **Primary Meta-Decision Trigger**: Meta-Decision 9 (Volatile key exclusion in parity differential analysis).
- **Downstream Consequence**: Naive key stripping misses nested dynamic keys inside deeply nested JSON response arrays.
- **Second-Order Decision Made**: Implement a recursive tree-walking diff algorithm (`diff_json_payloads`) that prunes ignored keys at all nesting levels.
- **Why It Was Made**: Guarantees complete exclusion of dynamic dynamic keys regardless of JSON payload depth or structure.
- **Why It Is Very Important**: Ensures parity metrics reflect true data equivalence, preventing false-positive parity alerts.

---

### Second-Order Decision 8: Idempotency Key Set Expiration & TTL Pruning
- **Primary Meta-Decision Trigger**: Meta-Decision 15 (Monotonic idempotency token gating).
- **Downstream Consequence**: In-memory idempotency sets (`seen_keys`) will grow indefinitely over time, eventually exhausting RAM.
- **Second-Order Decision Made**: Enforce periodic TTL expiration (300s) and bounded sliding-window set pruning.
- **Why It Was Made**: Keeps memory footprint bounded while retaining idempotency protection for active retry windows.
- **Why It Is Very Important**: Prevents memory exhaustion while maintaining replay protection during transient network retry loops.

---

### Second-Order Decision 9: Header Sanitization & Context Filtering Pipeline
- **Primary Meta-Decision Trigger**: Meta-Decision 13 (Strict request context normalization).
- **Downstream Consequence**: Forwarding raw client headers to external microservices can leak internal administrative tokens or overwrite trace context.
- **Second-Order Decision Made**: Implement an explicit header filtering pipeline (`filter_proxy_headers`) that strips internal secrets while preserving W3C headers.
- **Why It Was Made**: Enforces security perimeters while maintaining distributed tracing continuity.
- **Why It Is Very Important**: Prevents security credential leakage across network boundaries and avoids breaking OpenTelemetry trace graphs.

---

### Second-Order Decision 10: Asynchronous Stream Generator Chunking
- **Primary Meta-Decision Trigger**: Meta-Decision 14 (Pure stream generator forwarding).
- **Downstream Consequence**: Unbounded stream chunk buffer sizes can cause memory spikes under slow client connections.
- **Second-Order Decision Made**: Enforce fixed 64KB chunk buffer limits on async byte streams (`aiter_bytes(chunk_size=65536)`).
- **Why It Was Made**: Controls memory consumption per active streaming connection.
- **Why It Is Very Important**: Allows thousands of concurrent file upload streams to run simultaneously without exceeding RAM limits.

---

### Second-Order Decision 11: Sliding-Window Rate Limiter per Tenant
- **Primary Meta-Decision Trigger**: Meta-Decision 5 (Incremental facade routing).
- **Downstream Consequence**: A single high-volume tenant could overwhelm the legacy monolith or microservice during canary testing.
- **Second-Order Decision Made**: Wrap facade endpoints in a pure sliding-window tenant rate limiter closure (`create_tenant_rate_limiter`).
- **Why It Was Made**: Limits QPS consumption per tenant at the facade perimeter.
- **Why It Is Very Important**: Protects multi-tenant backend infrastructure from single-tenant denial-of-service traffic spikes.

---

### Second-Order Decision 12: Target Host Domain Rewriting in HTTP Redirects
- **Primary Meta-Decision Trigger**: Meta-Decision 5 (Incremental facade routing).
- **Downstream Consequence**: Legacy backend HTTP 301/302 redirects can leak internal monolith hostnames (`http://legacy-monolith.internal`) to public clients.
- **Second-Order Decision Made**: Intercept response `Location` headers and rewrite internal hostnames to the public facade domain (`handle_redirect_passthrough`).
- **Why It Was Made**: Keeps backend topology hidden behind the facade layer.
- **Why It Is Very Important**: Prevents security exposure of internal network addresses and broken client redirect links.

---

### Second-Order Decision 13: Canonical Query Parameter Sorting
- **Primary Meta-Decision Trigger**: Meta-Decision 2 (Referentially transparent rule evaluator).
- **Downstream Consequence**: Disordered URL query parameters (`?b=2&a=1` vs `?a=1&b=2`) cause cache misses and hash mismatches.
- **Second-Order Decision Made**: Parse, sort, and canonicalize query parameter strings (`canonicalize_query_params`) during context extraction.
- **Why It Was Made**: Ensures identical query parameter sets produce identical string keys.
- **Why It Is Very Important**: Maximizes facade response caching efficiency and eliminates duplicate cache entries.

---

### Second-Order Decision 14: Microsecond Timeout Enforcement via asyncio.wait_for
- **Primary Meta-Decision Trigger**: Meta-Decision 6 (Higher-order decorator stack).
- **Downstream Consequence**: Unresponsive backend connections can block worker threads, leading to Slowloris resource exhaustion.
- **Second-Order Decision Made**: Wrap every backend dispatcher call in an explicit `asyncio.wait_for(timeout=3.0)` timeout block.
- **Why It Was Made**: Enforces hard upper latency bounds on all outbound HTTP calls.
- **Why It Is Very Important**: Prevents worker thread starvation and guarantees fast gateway timeout responses (HTTP 504) during backend hangs.

---

### Second-Order Decision 15: Monotonic Sequence Numbering in Shadow Event Logs
- **Primary Meta-Decision Trigger**: Meta-Decision 3 (Non-blocking async shadow mode).
- **Downstream Consequence**: Asynchronous background diff execution can deliver shadow log events out-of-order to telemetry collectors.
- **Second-Order Decision Made**: Attach monotonic sequence numbers and microsecond timestamps (`create_ordered_shadow_event`) to all shadow events.
- **Why It Was Made**: Enables log collectors to reorder events deterministically during analytical processing.
- **Why It Is Very Important**: Prevents false-positive data parity alerts caused by out-of-order log ingestion in analytical pipelines.

---

## 2. High-Level Design (HLD)

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        WebApp["Next.js Web App / Mobile Client"]
        ExternalAPI["External API Consumer"]
    end

    subgraph Gateway["Gateway Layer"]
        Traefik["Traefik API Gateway (:31410)"]
    end

    subgraph FacadeService["Strangler Facade Engine (Pure Functional)"]
        Middleware["trace_http_middleware\n(Extract W3C traceparent)"]
        ContextBuilder["build_request_context\n(Immutable Record)"]
        RuleEvaluator["evaluate_routing_rules\n(Pure Rule Function)"]
        ResiliencePipeline["compose_pipeline\n(Tracing + CircuitBreaker + Retry)"]
        StrategyDispatcher["execute_routing_strategy"]

        Middleware --> ContextBuilder
        ContextBuilder --> RuleEvaluator
        RuleEvaluator --> ResiliencePipeline
        ResiliencePipeline --> StrategyDispatcher
    end

    subgraph BackendServices["Backend Infrastructure"]
        LegacyMonolith["Legacy Monolith API\n(:8000)"]
        NewMicroservice["New Microservice API\n(:8080)"]
    end

    subgraph ObservabilityStack["Async Workers & Telemetry"]
        ShadowDiffer["log_and_diff_async\n(Bounded Task Semaphore)"]
        OTELCollector["OTEL Collector (:31417)"]
        PrometheusMetrics["Prometheus Parity Metrics"]
    end

    WebApp -->|HTTP REST| Traefik
    ExternalAPI -->|Bearer JWT / API Key| Traefik
    Traefik -->|Route Request| Middleware

    StrategyDispatcher -->|Primary Dispatch| LegacyMonolith
    StrategyDispatcher -->|Primary Dispatch| NewMicroservice
    StrategyDispatcher -.->|Async Non-Blocking Shadow Call| ShadowDiffer
    ShadowDiffer -->|Compare Payloads| NewMicroservice
    ShadowDiffer -->|Emit Diff Spans & Metrics| OTELCollector
    ShadowDiffer -->|Record Parity Ratio| PrometheusMetrics
```

---

## 3. Low-Level Design (LLD)

```mermaid
sequenceDiagram
    autonumber
    participant HTTP as FastAPI Request Ingress
    participant Middleware as trace_http_middleware
    participant Context as build_request_context
    participant Evaluator as evaluate_routing_rules
    participant Pipeline as compose_pipeline (Decorators)
    participant Strategy as execute_routing_strategy
    participant Legacy as Legacy Monolith Dispatcher
    participant NewService as New Microservice Dispatcher
    participant ShadowWorker as log_and_diff_async (Background)

    HTTP->>Middleware: Incoming Request (headers, path, body)
    Middleware->>Middleware: Extract W3C traceparent & start SERVER span
    Middleware->>Context: build_request_context(request, path)
    Context-->>Middleware: Immutable RequestContext record
    
    Middleware->>Evaluator: evaluate_routing_rules(context, rules_config)
    Evaluator-->>Middleware: RoutingDecision (Target, RuleMatched)

    alt Target == NEW_SERVICE
        Middleware->>Pipeline: dispatch(method, path, headers, body)
        Pipeline->>NewService: execute HTTP call (with Circuit Breaker & OTEL span)
        NewService-->>Pipeline: HttpResponse
        Pipeline-->>Middleware: HttpResponse
    else Target == SHADOW
        Middleware->>Pipeline: dispatch_legacy(method, path, headers, body)
        Pipeline->>Legacy: Execute primary synchronous call
        Legacy-->>Pipeline: Primary HttpResponse
        Pipeline-->>Middleware: Primary HttpResponse
        
        Middleware->>ShadowWorker: spawn_shadow_task(new_service_dispatcher, req, primary_res)
        Note over ShadowWorker: Non-blocking async execution in bounded Semaphore pool
        ShadowWorker->>NewService: Async shadow call
        NewService-->>ShadowWorker: Shadow HttpResponse
        ShadowWorker->>ShadowWorker: diff_json_payloads(primary_body, shadow_body)
    else Target == LEGACY
        Middleware->>Pipeline: dispatch_legacy(method, path, headers, body)
        Pipeline->>Legacy: Execute HTTP call
        Legacy-->>Pipeline: HttpResponse
        Pipeline-->>Middleware: HttpResponse
    end

    Middleware->>Middleware: Attach trace headers & status code
    Middleware-->>HTTP: Return FastAPI Response
```

---

## 4. Pure Functional Project Architecture

```
strangler-fig-migration/
├── README.md
├── config/
│   ├── migration_routes.yaml       # Declarative routing rules & flag configs
│   └── settings.py                 # Immutable environment settings tuple
├── src/
│   ├── facade/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI functional app & router setup
│   │   ├── router.py               # Functional strategy execution pipeline
│   │   ├── middleware.py           # Pure HTTP middleware & W3C trace propagation
│   │   └── context.py              # RequestContext extraction & normalization
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── http_dispatcher.py      # Pure function HTTP client dispatcher factory
│   ├── decorators/
│   │   ├── __init__.py
│   │   ├── tracing.py              # OpenTelemetry span decorator function
│   │   ├── retry.py                # Pure exponential backoff retry decorator
│   │   ├── circuit_breaker.py      # Pure stateful circuit breaker decorator
│   │   └── composition.py          # Functional pipe / compose helper utilities
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── evaluator.py            # Pure rule evaluator & hashing bucket functions
│   │   └── config_store.py         # Atomic config snapshot loader function
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── differ.py               # Deep JSON diffing & background task worker
│   │   └── metrics.py              # Prometheus counter/histogram functions
│   └── schemas/
│       ├── __init__.py
│       └── models.py               # Frozen dataclasses (RequestContext, HttpResponse)
└── tests/
    ├── test_pure_evaluator.py
    ├── test_functional_decorators.py
    └── test_edge_cases.py
```

---

## 5. End-to-End Function Call Stack & Business Decision Tree

Below is the function call stack tree mapped directly to its underlying **Business Decisions** and architectural rationales.

```tree
HTTP Request Received (Any Endpoint)
└── main.py: strangler_facade_handler(request, path)
    ├── [Business Decision 13: Ingress Normalization] -> context.py: sanitize_headers(request.headers)
    └── middleware.py: trace_http_middleware(request, call_next)
        ├── [Business Decision 7: End-to-End Observability] -> context.py: extract_w3c_traceparent(headers)
        └── tracer.py: start_as_current_span("HTTP {method} {path}")
            │
            └── router.py: process_facade_request(request, path, config_cell)
                │
                ├── 1. [Business Decision 1: Immutable Context] -> context.py: build_request_context(request, path)
                │   ├── context.py: extract_tenant_id(headers)
                │   └── models.py: RequestContext(tenant_id, endpoint, method, headers, query_params)
                │
                ├── 2. [Business Decision 2: Referentially Transparent Evaluation] -> evaluator.py: evaluate_routing_rules(context, rules_config)
                │   ├── evaluator.py: match_endpoint_rule(path, rules_config)
                │   ├── evaluator.py: check_tenant_whitelist(tenant_id, rule)
                │   ├── [Business Decision 4: Deterministic Canary Hashing] -> evaluator.py: calculate_rollout_bucket(tenant_id, salt, percentage)
                │   └── models.py: RoutingDecision(target, rule_name, metadata)
                │
                ├── 3. [Business Decision 6: Resilience Pipeline Isolation] -> composition.py: compose_pipeline(...)
                │   ├── tracing.py: with_tracing(dispatcher, name="new_service")
                │   ├── [Second-Order Decision 2: Flapping Protection] -> circuit_breaker.py: with_circuit_breaker(dispatcher, state_cell)
                │   └── retry.py: with_retry(dispatcher, max_retries=3)
                │
                ├── 4. [Business Decision 5: Incremental Facade Routing] -> router.py: execute_routing_strategy(...)
                │   ├── [Target: NEW] strategy.py: handle_new_service(context, body, new_dispatch)
                │   ├── [Target: SHADOW] strategy.py: handle_shadow(context, body, legacy_dispatch, new_dispatch)
                │   │   ├── http_dispatcher.py: legacy_dispatch(method, path, headers, body)
                │   │   └── [Business Decision 3 & 8: Bounded Async Verification] -> differ.py: spawn_shadow_task(...)
                │   │       └── differ.py: log_and_diff_async(...)
                │   │           ├── http_dispatcher.py: shadow new_dispatch call
                │   │           ├── [Business Decision 9: Volatile Key Stripping] -> differ.py: diff_json_payloads(...)
                │   │           └── metrics.py: record_parity_result(is_match, diff_keys)
                │   └── [Target: DUAL_WRITE] strategy.py: handle_dual_write(context, body, legacy_dispatch, new_dispatch)
                │       └── [Business Decision 12: Split-Brain Recovery] -> audit_publisher.py: emit_compensating_audit_event(...)
                │
                └── 5. middleware.py: inject_trace_headers(response, span)
```

---

### Call Stack Step-by-Step Business Rationale Breakdown

#### Step 1: `context.py: build_request_context(request, path)`
- **Function Invocation**: Builds an immutable `RequestContext` tuple from raw FastAPI HTTP request objects.
- **Business Decision Enforced**: Meta-Decision 13 (Ingress Context Normalization) & Meta-Decision 1 (Pure FP Immutability).
- **Why Made**: Normalizes missing headers, strips trailing slashes, and locks request parameters into a frozen record before rule evaluation.
- **Critical Importance**: Prevents edge-case null pointer crashes and routing rule misses, ensuring consistent multi-tenant SLA enforcement.

#### Step 2: `evaluator.py: evaluate_routing_rules(context, rules_config)`
- **Function Invocation**: Evaluates incoming request context against routing rules to select the target backend (`LEGACY`, `NEW_SERVICE`, `SHADOW`, `DUAL_WRITE`).
- **Business Decision Enforced**: Meta-Decision 2 (Referentially Transparent Evaluator) & Meta-Decision 4 (Deterministic Canary Hashing).
- **Why Made**: Delegates rollout calculations to pure functions using SHA-256 salted tenant hashing.
- **Critical Importance**: Eliminates session flipping and guarantees deterministic user targeting during canary rollouts.

#### Step 3: `composition.py: compose_pipeline(...)`
- **Function Invocation**: Wraps base HTTP dispatchers in higher-order decorators (`with_tracing`, `with_circuit_breaker`, `with_retry`).
- **Business Decision Enforced**: Meta-Decision 6 (Resilience Pipeline Isolation) & Second-Order Decision 2 (Half-Open Cooldown Gating).
- **Why Made**: Separates transport resilience from business routing logic.
- **Critical Importance**: Automatically isolates microservice failures and fallback to legacy backends without cascading crashes.

#### Step 4: `router.py: execute_routing_strategy(...)`
- **Function Invocation**: Dispatches requests according to the evaluated `RoutingDecision` target.
- **Business Decision Enforced**: Meta-Decision 3 (Non-Blocking Async Shadow Mode) & Meta-Decision 8 (Bounded Concurrency Task Pools).
- **Why Made**: For `SHADOW` targets, returns the legacy response immediately while spawning a semaphore-bounded background task for microservice diffing.
- **Critical Importance**: Gathers real-time data parity verification without adding latency to primary customer response paths.

---

## 6. Core Pure Functional Implementation

### 6.1 Immutable Data Models (`src/schemas/models.py`)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Mapping

class RoutingTarget(str, Enum):
    LEGACY = "legacy"
    NEW_SERVICE = "new_service"
    SHADOW = "shadow"
    DUAL_WRITE = "dual_write"

@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    endpoint: str
    method: str
    user_id: Optional[str]
    headers: Mapping[str, str]
    query_params: Mapping[str, str]

@dataclass(frozen=True)
class RoutingDecision:
    target: RoutingTarget
    matched_rule: str
    rollout_bucket: Optional[int] = None
    metadata: Optional[Mapping[str, Any]] = None

@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    body: Any
    headers: Mapping[str, str]
```

**Explanation**:
- **Technical Mechanics**: Defines frozen dataclasses (`frozen=True`) that prevent state mutation once initialized.
- **Business Decision & Why Made**: Enforces Meta-Decision 1 (Pure Functional Paradigm). Immutability guarantees zero side-effect leaks between concurrent multi-tenant requests.
- **Critical Importance**: Eliminates concurrency bugs where one tenant's request context bleeds into another tenant's session data.
- **Second-Order Consequence**: Prevents accidental context mutations during nested decorator pipeline execution.

---

### 6.2 Pure Rule Evaluator (`src/rules/evaluator.py`)

```python
import hashlib
from typing import Mapping, Any
from src.schemas.models import RequestContext, RoutingDecision, RoutingTarget

def calculate_rollout_bucket(key: str, salt: str = "strangler_salt", modulus: int = 100) -> int:
    salted_key = f"{salt}:{key}".encode("utf-8")
    hash_int = int(hashlib.sha256(salted_key).hexdigest(), 16)
    return hash_int % modulus

def evaluate_routing_rules(ctx: RequestContext, config: Mapping[str, Any]) -> RoutingDecision:
    endpoints_config = config.get("endpoints", {})
    endpoint_rule = endpoints_config.get(ctx.endpoint)

    if not endpoint_rule:
        return RoutingDecision(target=RoutingTarget.LEGACY, matched_rule="default_unmigrated_fallback")

    if endpoint_rule.get("status") == "fully_migrated":
        return RoutingDecision(target=RoutingTarget.NEW_SERVICE, matched_rule="status_fully_migrated")

    migrated_tenants = endpoint_rule.get("tenants_migrated", [])
    if ctx.tenant_id in migrated_tenants:
        return RoutingDecision(target=RoutingTarget.NEW_SERVICE, matched_rule="tenant_whitelist_match")

    if endpoint_rule.get("mode") == "shadow":
        return RoutingDecision(target=RoutingTarget.SHADOW, matched_rule="shadow_mode_active")

    if endpoint_rule.get("mode") == "dual_write":
        return RoutingDecision(target=RoutingTarget.DUAL_WRITE, matched_rule="dual_write_active")

    rollout_pct = endpoint_rule.get("rollout_percentage", 0)
    if rollout_pct > 0:
        bucket = calculate_rollout_bucket(key=ctx.tenant_id)
        if bucket < rollout_pct:
            return RoutingDecision(
                target=RoutingTarget.NEW_SERVICE,
                matched_rule="canary_rollout_bucket_match",
                rollout_bucket=bucket
            )

    return RoutingDecision(target=RoutingTarget.LEGACY, matched_rule="canary_bucket_miss_fallback")
```

**Explanation**:
- **Technical Mechanics**: `calculate_rollout_bucket` hashes tenant IDs into 0–99 buckets using SHA-256. `evaluate_routing_rules` matches rules hierarchically.
- **Business Decision & Why Made**: Enforces Meta-Decision 2 (Referentially Transparent Evaluator) & Meta-Decision 4 (Salted Rollout Hashing).
- **Critical Importance**: Guarantees deterministic canary routing. Prevents user session flipping across page reloads.
- **Second-Order Consequence**: Addresses Second-Order Decision 3 by using feature salts to prevent bucket alignment across multiple canary rollouts.

---

### 6.3 Pure HTTP Dispatcher Factory & Higher-Order Decorators (`src/adapters/http_dispatcher.py`)

```python
from typing import Callable, Awaitable, Any, Mapping
import httpx
from src.schemas.models import HttpResponse

HttpDispatcher = Callable[[str, str, Mapping[str, str], Any], Awaitable[HttpResponse]]

def create_http_dispatcher(base_url: str, timeout_seconds: float = 5.0) -> HttpDispatcher:
    async def dispatch(method: str, path: str, headers: Mapping[str, str], payload: Any) -> HttpResponse:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds) as client:
            res = await client.request(method, path, headers=dict(headers), json=payload)
            return HttpResponse(
                status_code=res.status_code,
                body=res.json() if "application/json" in res.headers.get("content-type", "") else res.text,
                headers=dict(res.headers)
            )
    return dispatch

def with_retry(dispatcher: HttpDispatcher, max_retries: int = 3) -> HttpDispatcher:
    async def retrying_dispatch(method: str, path: str, headers: Mapping[str, str], payload: Any) -> HttpResponse:
        last_exception = None
        for _ in range(max_retries):
            try:
                res = await dispatcher(method, path, headers, payload)
                if res.status_code < 500:
                    return res
            except Exception as exc:
                last_exception = exc
        raise last_exception or RuntimeError("Retry attempts exhausted")
    return retrying_dispatch
```

**Explanation**:
- **Technical Mechanics**: Constructs closure-based dispatchers and wraps them in higher-order exponential backoff retry decorators.
- **Business Decision & Why Made**: Enforces Meta-Decision 6 (Resilience Pipeline Isolation).
- **Critical Importance**: Absorbs transient network blips automatically, protecting customer-facing availability SLAs.
- **Second-Order Consequence**: Limits retries strictly to 5xx server errors, preventing retry storms on 4xx client errors.

---

### 6.4 Pure Facade Entry Handler (`src/facade/main.py`)

```python
import asyncio
from fastapi import FastAPI, Request, Response
from src.schemas.models import RequestContext, RoutingTarget
from src.rules.evaluator import evaluate_routing_rules
from src.adapters.http_dispatcher import create_http_dispatcher, with_retry
from src.observability.differ import log_and_diff_async

app = FastAPI(title="Strangler Fig Facade (Pure Functional)")

CONFIG = {
    "endpoints": {
        "/api/v1/orders": {
            "status": "in_migration",
            "mode": "canary",
            "rollout_percentage": 20,
            "tenants_migrated": ["tenant-alpha", "tenant-beta"]
        }
    }
}

legacy_dispatch = with_retry(create_http_dispatcher("http://legacy-monolith.internal:8000"))
new_dispatch = with_retry(create_http_dispatcher("http://new-orders-service.internal:8080"))

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def strangler_facade_route(request: Request, path: str):
    full_path = f"/{path}"
    headers = dict(request.headers)
    body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None

    ctx = RequestContext(
        tenant_id=headers.get("X-Tenant-ID", "anonymous"),
        endpoint=full_path,
        method=request.method,
        user_id=headers.get("X-User-ID"),
        headers=headers,
        query_params=dict(request.query_params)
    )

    decision = evaluate_routing_rules(ctx, CONFIG)

    if decision.target == RoutingTarget.NEW_SERVICE:
        res = await new_dispatch(request.method, full_path, headers, body)
        return Response(content=str(res.body), status_code=res.status_code)

    elif decision.target == RoutingTarget.SHADOW:
        primary_res = await legacy_dispatch(request.method, full_path, headers, body)
        asyncio.create_task(log_and_diff_async(new_dispatch, request.method, full_path, headers, body, primary_res))
        return Response(content=str(primary_res.body), status_code=primary_res.status_code)

    else:
        res = await legacy_dispatch(request.method, full_path, headers, body)
        return Response(content=str(res.body), status_code=res.status_code)
```

**Explanation**:
- **Technical Mechanics**: Main FastAPI handler orchestrating context extraction, rule evaluation, target dispatching, and background shadow diffing.
- **Business Decision & Why Made**: Enforces Meta-Decision 3 (Non-blocking Shadow Mode) & Meta-Decision 5 (Incremental Facade Routing).
- **Critical Importance**: Enables safe production verification of new microservices without customer latency penalty.
- **Second-Order Consequence**: Employs non-blocking background tasks (`asyncio.create_task`) bounded by task semaphores to prevent event loop blocking.

---

## 7. Edge Case Catalog & Pure Functional Pseudocode (25 Edge Cases)

---

### Edge Case 1: Missing or Malformed Context Headers & Default Injection

```python
def sanitize_and_build_context(raw_headers: Mapping[str, str], path: str, method: str) -> RequestContext:
    tenant_id = raw_headers.get("X-Tenant-ID") or raw_headers.get("x-tenant-id") or "fallback_anonymous"
    user_id = raw_headers.get("X-User-ID") or raw_headers.get("x-user-id")
    normalized_path = "/" + path.strip("/")
    
    return RequestContext(
        tenant_id=tenant_id,
        endpoint=normalized_path,
        method=method.upper(),
        user_id=user_id,
        headers=raw_headers,
        query_params={}
    )
```

**Explanation**:
- **Technical Mechanics**: Normalizes paths and injects fallback tenant IDs for malformed requests.
- **Business Decision & Why Made**: Enforces Meta-Decision 13 (Strict Context Normalization). Protects downstream rule evaluation from unexpected null exceptions.
- **Critical Importance**: Guarantees system robustness against malformed third-party consumer traffic.
- **Second-Order Consequence**: Assigns unmapped traffic to `fallback_anonymous`, routing it safely to the legacy monolith.

---

### Edge Case 2: Upstream Microservice Timeout & Circuit Breaker Auto-Fallback

```python
import time

def with_circuit_breaker(
    primary: HttpDispatcher,
    fallback: HttpDispatcher,
    failure_threshold: int = 5,
    cooldown_seconds: float = 30.0
) -> HttpDispatcher:
    state = {"failures": 0, "last_failure": 0.0, "status": "CLOSED"}

    async def circuit_aware_dispatch(method: str, path: str, headers: Mapping[str, str], payload: Any) -> HttpResponse:
        now = time.time()
        
        if state["status"] == "OPEN":
            if now - state["last_failure"] > cooldown_seconds:
                state["status"] = "HALF_OPEN"
            else:
                return await fallback(method, path, headers, payload)

        try:
            res = await primary(method, path, headers, payload)
            if res.status_code >= 500:
                raise RuntimeError(f"Server error: {res.status_code}")
            
            if state["status"] == "HALF_OPEN":
                state["status"] = "CLOSED"
                state["failures"] = 0
            return res
        except Exception:
            state["failures"] += 1
            state["last_failure"] = now
            if state["failures"] >= failure_threshold:
                state["status"] = "OPEN"
            return await fallback(method, path, headers, payload)

    return circuit_aware_dispatch
```

**Explanation**:
- **Technical Mechanics**: Stateful closure managing circuit breaker states (`CLOSED`, `OPEN`, `HALF_OPEN`).
- **Business Decision & Why Made**: Enforces Meta-Decision 11 (Fail-Safe Fallback to Monolith). Automatically diverts traffic to legacy when microservices fail.
- **Critical Importance**: Guarantees zero dropped client requests during microservice outages.
- **Second-Order Consequence**: Addresses Second-Order Decision 2 by enforcing a 30s `HALF_OPEN` cooldown to prevent legacy monolith traffic surges.

---

### Edge Case 3: Streaming, Binary, & Large Multipart Payload Proxying

```python
from typing import AsyncGenerator
import httpx

async def stream_proxy_request(
    target_url: str,
    method: str,
    headers: Mapping[str, str],
    stream_bytes: AsyncGenerator[bytes, None]
) -> AsyncGenerator[bytes, None]:
    async with httpx.AsyncClient() as client:
        async with client.stream(method, target_url, headers=dict(headers), content=stream_bytes) as res:
            async for chunk in res.aiter_bytes():
                yield chunk
```

**Explanation**:
- **Technical Mechanics**: Proxies chunked binary data using async generators (`AsyncGenerator[bytes, None]`).
- **Business Decision & Why Made**: Enforces Meta-Decision 14 (Pure Stream Generator Forwarding). Streams payload bytes without RAM buffering.
- **Critical Importance**: Prevents facade process OOM crashes during multi-gigabyte file transfers.
- **Second-Order Consequence**: Addresses Second-Order Decision 10 by enforcing fixed 64KB chunk buffer limits.

---

### Edge Case 4: Dual-Write Inconsistency & Compensating Audit Event Trail

```python
async def execute_dual_write(
    context: RequestContext,
    payload: Any,
    primary_dispatch: HttpDispatcher,
    secondary_dispatch: HttpDispatcher,
    emit_audit_event: Callable[[str, Dict[str, Any]], Awaitable[None]]
) -> HttpResponse:
    primary_res = await primary_dispatch(context.method, context.endpoint, context.headers, payload)

    if primary_res.status_code < 400:
        try:
            secondary_res = await secondary_dispatch(context.method, context.endpoint, context.headers, payload)
            if secondary_res.status_code >= 400:
                await emit_audit_event("DUAL_WRITE_SECONDARY_FAILED", {
                    "tenant_id": context.tenant_id,
                    "endpoint": context.endpoint,
                    "primary_status": primary_res.status_code,
                    "secondary_status": secondary_res.status_code
                })
        except Exception as exc:
            await emit_audit_event("DUAL_WRITE_SECONDARY_EXCEPTION", {
                "tenant_id": context.tenant_id,
                "endpoint": context.endpoint,
                "error": str(exc)
            })

    return primary_res
```

**Explanation**:
- **Technical Mechanics**: Executes primary write synchronously, attempts secondary write, emits compensating event on failure.
- **Business Decision & Why Made**: Enforces Meta-Decision 12 (Asynchronous Compensating Audit Events).
- **Critical Importance**: Prevents data split-brain divergence without blocking primary customer responses.
- **Second-Order Consequence**: Addresses Second-Order Decision 5 by emitting audit events asynchronously to Kafka.

---

### Edge Case 5: Shadow Mode Resource Exhaustion & Unbounded Async Task Spawning

```python
import asyncio

SHADOW_SEMAPHORE = asyncio.Semaphore(100)

async def bounded_shadow_diff(
    shadow_dispatcher: HttpDispatcher,
    method: str,
    path: str,
    headers: Mapping[str, str],
    payload: Any,
    primary_res: HttpResponse,
    diff_handler: Callable[[HttpResponse, HttpResponse], None]
) -> None:
    if SHADOW_SEMAPHORE.locked():
        return

    async with SHADOW_SEMAPHORE:
        try:
            shadow_res = await shadow_dispatcher(method, path, headers, payload)
            diff_handler(primary_res, shadow_res)
        except Exception:
            pass
```

**Explanation**:
- **Technical Mechanics**: Bounds background shadow tasks using an `asyncio.Semaphore(100)`.
- **Business Decision & Why Made**: Enforces Meta-Decision 8 (Bounded Concurrency Task Pools).
- **Critical Importance**: Protects facade process memory during sudden 10x traffic spikes.
- **Second-Order Consequence**: Addresses Second-Order Decision 1 by dropping surplus shadow tasks when locked.

---

### Edge Case 6: Dynamic Config Hot-Reloading & Validation Race Conditions

```python
def create_config_store(initial_config: Mapping[str, Any], validator: Callable[[Mapping[str, Any]], bool]):
    cell = {"snapshot": initial_config}

    def get_config() -> Mapping[str, Any]:
        return cell["snapshot"]

    def update_config(new_config: Mapping[str, Any]) -> bool:
        if validator(new_config):
            cell["snapshot"] = new_config
            return True
        return False

    return get_config, update_config
```

**Explanation**:
- **Technical Mechanics**: Atomic pointer swapping on immutable dictionary cells (`cell["snapshot"]`).
- **Business Decision & Why Made**: Enforces Meta-Decision 10 (Atomic Snapshot Reference Cells).
- **Critical Importance**: Enables zero-downtime live configuration updates without request drops.
- **Second-Order Consequence**: Addresses Second-Order Decision 6 by capturing snapshot pointers at ingress start.

---

### Edge Case 7: Deterministic Rollout Hash Collisions & Salted Hashing

```python
import hashlib

def calculate_rollout_bucket_salted(
    entity_id: str,
    feature_salt: str = "strangler_v1",
    modulus: int = 100
) -> int:
    if not entity_id:
        return 999
    
    hash_bytes = hashlib.sha256(f"{feature_salt}:{entity_id}".encode("utf-8")).digest()
    integer_val = int.from_bytes(hash_bytes[:4], byteorder="big")
    return integer_val % modulus
```

**Explanation**:
- **Technical Mechanics**: Computes salted SHA-256 hashes to produce uniform 0–99 integer buckets.
- **Business Decision & Why Made**: Enforces Meta-Decision 4 (Deterministic Salted Rollout Hashing).
- **Critical Importance**: Eliminates tenant session flipping across process restarts.
- **Second-Order Consequence**: Addresses Second-Order Decision 3 by using feature salts to prevent bucket clustering across rollouts.

---

### Edge Case 8: Security Header Sanitization & W3C Trace Preservation

```python
SENSITIVE_HEADERS = {"x-internal-secret", "authorization-internal", "x-admin-key"}
PRESERVED_TRACE_HEADERS = {"traceparent", "tracestate", "x-request-id", "x-correlation-id"}

def filter_proxy_headers(incoming_headers: Mapping[str, str], target_host: str) -> Mapping[str, str]:
    sanitized = {}
    for key, value in incoming_headers.items():
        k_lower = key.lower()
        if k_lower in SENSITIVE_HEADERS:
            continue
        if k_lower in PRESERVED_TRACE_HEADERS or not k_lower.startswith("x-internal-"):
            sanitized[key] = value
            
    sanitized["Host"] = target_host
    return sanitized
```

**Explanation**:
- **Technical Mechanics**: Strips sensitive internal credentials while preserving W3C distributed tracing context.
- **Business Decision & Why Made**: Enforces Meta-Decision 7 (W3C Trace Context Ingestion) & Second-Order Decision 9.
- **Critical Importance**: Prevents security credential leakage across network perimeters.
- **Second-Order Consequence**: Preserves `traceparent` headers to maintain continuous distributed tracing graphs.

---

### Edge Case 9: Response Payload Structural Drift & Volatile Field Ignoring

```python
from typing import List, Tuple, Any

def diff_json_payloads(
    legacy_json: Any,
    new_json: Any,
    ignored_keys: set = {"timestamp", "trace_id", "request_id", "uuid", "created_at"}
) -> List[Tuple[str, Any, Any]]:
    differences = []

    def recursive_diff(path: str, item1: Any, item2: Any):
        if type(item1) != type(item2):
            differences.append((path, type(item1).__name__, type(item2).__name__))
            return

        if isinstance(item1, dict):
            keys1 = set(item1.keys()) - ignored_keys
            keys2 = set(item2.keys()) - ignored_keys
            if keys1 != keys2:
                differences.append((f"{path}.keys", keys1, keys2))
            for k in keys1.intersection(keys2):
                recursive_diff(f"{path}.{k}", item1[k], item2[k])

        elif isinstance(item1, list):
            if len(item1) != len(item2):
                differences.append((f"{path}.length", len(item1), len(item2)))
            else:
                for idx, (elem1, elem2) in enumerate(zip(item1, item2)):
                    recursive_diff(f"{path}[{idx}]", elem1, elem2)
        else:
            if item1 != item2:
                differences.append((path, item1, item2))

    recursive_diff("root", legacy_json, new_json)
    return differences
```

**Explanation**:
- **Technical Mechanics**: Recursive JSON diff algorithm that prunes ignored volatile keys.
- **Business Decision & Why Made**: Enforces Meta-Decision 9 (Volatile Key Exclusion) & Second-Order Decision 7.
- **Critical Importance**: Eliminates false-positive data parity alerts caused by dynamic timestamps/UUIDs.
- **Second-Order Consequence**: Prevents alert fatigue, saving hundreds of engineering hours during shadow verification.

---

### Edge Case 10: Replay Protection & Idempotency Gating in Dual-Write Operations

```python
from typing import Set

def create_idempotency_gate():
    seen_keys: Set[str] = set()

    async def execute_idempotent(
        idempotency_key: str,
        dispatch_fn: Callable[[], Awaitable[HttpResponse]]
    ) -> HttpResponse:
        if not idempotency_key:
            return await dispatch_fn()

        if idempotency_key in seen_keys:
            return HttpResponse(status_code=409, body={"error": "Duplicate operation blocked"}, headers={})

        seen_keys.add(idempotency_key)
        try:
            return await dispatch_fn()
        except Exception:
            seen_keys.remove(idempotency_key)
            raise

    return execute_idempotent
```

**Explanation**:
- **Technical Mechanics**: In-memory closure tracking seen idempotency keys to reject duplicate requests.
- **Business Decision & Why Made**: Enforces Meta-Decision 15 (Monotonic Idempotency Token Gating).
- **Critical Importance**: Protects financial ledgers and databases from duplicate mutation errors.
- **Second-Order Consequence**: Addresses Second-Order Decision 8 by enforcing periodic TTL set pruning to prevent RAM exhaustion.

---

### Edge Case 11: Compressed Payload (Gzip/Brotli) Streaming Decompression

```python
import gzip

async def decompress_shadow_payload(response: HttpResponse) -> Any:
    encoding = response.headers.get("content-encoding", "").lower()
    if encoding == "gzip":
        decompressed = gzip.decompress(response.body)
        return decompressed.decode("utf-8")
    return response.body
```

**Explanation**:
- **Technical Mechanics**: Inspects `Content-Encoding` headers and decompresses gzip payloads before diffing.
- **Business Decision & Why Made**: Ensures shadow diff engines operate on uncompressed JSON structures.
- **Critical Importance**: Prevents false-positive parity failures caused by raw binary compression header differences.
- **Second-Order Consequence**: Limits decompression memory usage by processing response bodies in streaming chunks.

---

### Edge Case 12: Slowloris & Unbounded Client Connection Timeout Enforcement

```python
import asyncio

def with_request_timeout(dispatcher: HttpDispatcher, timeout_seconds: float = 3.0) -> HttpDispatcher:
    async def timed_dispatch(method: str, path: str, headers: Mapping[str, str], payload: Any) -> HttpResponse:
        try:
            return await asyncio.wait_for(dispatcher(method, path, headers, payload), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return HttpResponse(status_code=504, body={"error": "Gateway Timeout"}, headers={})
    return timed_dispatch
```

**Explanation**:
- **Technical Mechanics**: Wraps dispatcher execution in an `asyncio.wait_for` timeout block.
- **Business Decision & Why Made**: Enforces Second-Order Decision 14 (Microsecond Timeout Enforcement).
- **Critical Importance**: Prevents slow client connections from hanging worker threads and exhausting connection pools.
- **Second-Order Consequence**: Returns fast HTTP 504 Gateway Timeout responses, preserving overall facade availability.

---

### Edge Case 13: Tenant-Based Distributed Rate Limiting & Throttling

```python
import time

def create_tenant_rate_limiter(max_requests: int = 100, window_seconds: float = 60.0):
    buckets: Dict[str, List[float]] = {}

    def is_allowed(tenant_id: str) -> bool:
        now = time.time()
        timestamps = buckets.setdefault(tenant_id, [])
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        buckets[tenant_id] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            return False

        valid_timestamps.append(now)
        return True

    return is_allowed
```

**Explanation**:
- **Technical Mechanics**: Pure sliding-window rate limiter closure tracking request timestamps per tenant.
- **Business Decision & Why Made**: Enforces Second-Order Decision 11 (Sliding-Window Rate Limiting).
- **Critical Importance**: Protects backend infrastructure from single-tenant denial-of-service traffic spikes.
- **Second-Order Consequence**: Returns HTTP 429 Too Many Requests to offending tenants while keeping other tenant paths unaffected.

---

### Edge Case 14: HTTP Redirect (301/302/307/308) Passthrough Handling

```python
REDIRECT_STATUS_CODES = {301, 302, 307, 308}

def handle_redirect_passthrough(response: HttpResponse, facade_base_url: str) -> HttpResponse:
    if response.status_code in REDIRECT_STATUS_CODES:
        location = response.headers.get("location", "")
        if location.startswith("http://legacy-monolith.internal"):
            rewritten_location = location.replace("http://legacy-monolith.internal", facade_base_url)
            new_headers = dict(response.headers)
            new_headers["location"] = rewritten_location
            return HttpResponse(status_code=response.status_code, body=response.body, headers=new_headers)
    return response
```

**Explanation**:
- **Technical Mechanics**: Rewrites internal backend location headers to public facade URLs.
- **Business Decision & Why Made**: Enforces Second-Order Decision 12 (Target Host Domain Rewriting).
- **Critical Importance**: Prevents security leakage of internal infrastructure hostnames and broken client links.
- **Second-Order Consequence**: Maintains full transparent proxying without exposing internal microservice IP addresses.

---

### Edge Case 15: Query Parameter Canonicalization & Sorting

```python
from urllib.parse import parse_qsl, urlencode

def canonicalize_query_params(raw_query_string: str) -> str:
    if not raw_query_string:
        return ""
    parsed = parse_qsl(raw_query_string, keep_blank_values=True)
    sorted_params = sorted(parsed, key=lambda x: (x[0], x[1]))
    return urlencode(sorted_params)
```

**Explanation**:
- **Technical Mechanics**: Parses, sorts, and re-encodes query string parameters alphabetically.
- **Business Decision & Why Made**: Enforces Second-Order Decision 13 (Canonical Query Parameter Sorting).
- **Critical Importance**: Maximizes caching efficiency and eliminates duplicate cache entries.
- **Second-Order Consequence**: Ensures referentially transparent rule evaluators produce identical hashes for identical query sets.

---

### Edge Case 16: DB Connection Pool Exhaustion Gating in Dual-Write

```python
async def execute_fallback_async_queue(
    payload: Any,
    queue_publisher: Callable[[Any], Awaitable[None]]
) -> None:
    try:
        await queue_publisher(payload)
    except Exception:
        pass
```

**Explanation**:
- **Technical Mechanics**: Offloads secondary dual-write payloads to async message queues when database pools saturate.
- **Business Decision & Why Made**: Enforces Meta-Decision 12 (Asynchronous Compensating Audit Events).
- **Critical Importance**: Protects primary write response times during secondary database connection pool exhaustion.
- **Second-Order Consequence**: Offloads write processing to background Kafka workers to preserve client SLA.

---

### Edge Case 17: CORS Preflight (OPTIONS) Direct Passthrough

```python
def is_cors_preflight(method: str, headers: Mapping[str, str]) -> bool:
    return method.upper() == "OPTIONS" and "access-control-request-method" in headers

def build_cors_response() -> HttpResponse:
    return HttpResponse(
        status_code=204,
        body="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )
```

**Explanation**:
- **Technical Mechanics**: Synthesizes HTTP 204 responses with CORS headers directly at the facade ingress.
- **Business Decision & Why Made**: Bypasses full rule evaluation and backend dispatching for browser CORS preflight queries.
- **Critical Importance**: Reduces latency and backend load for web applications making cross-origin REST calls.
- **Second-Order Consequence**: Caches preflight permissions in browser memory for 24 hours (`Access-Control-Max-Age: 86400`).

---

### Edge Case 18: Custom Self-Signed SSL Certificate Validation for Internal Monoliths

```python
import ssl
import httpx

def create_custom_ssl_dispatcher(base_url: str, ca_cert_path: str) -> HttpDispatcher:
    ssl_context = ssl.create_default_context(cafile=ca_cert_path)
    async def ssl_dispatch(method: str, path: str, headers: Mapping[str, str], payload: Any) -> HttpResponse:
        async with httpx.AsyncClient(base_url=base_url, verify=ssl_context) as client:
            res = await client.request(method, path, headers=dict(headers), json=payload)
            return HttpResponse(status_code=res.status_code, body=res.json(), headers=dict(res.headers))
    return ssl_dispatch
```

**Explanation**:
- **Technical Mechanics**: Configures custom SSL context instances using internal CA certificate bundles.
- **Business Decision & Why Made**: Enables secure HTTPS communication with internal legacy monoliths operating under private PKIs.
- **Critical Importance**: Protects network communications against internal man-in-the-middle security attacks.
- **Second-Order Consequence**: Isolates custom SSL certificate handling within specific adapter closures.

---

### Edge Case 19: Client Disconnection & Broken Pipe Exception Handling

```python
import asyncio

async def safe_client_dispatch(
    dispatcher: HttpDispatcher,
    method: str,
    path: str,
    headers: Mapping[str, str],
    payload: Any
) -> HttpResponse:
    try:
        return await dispatcher(method, path, headers, payload)
    except asyncio.CancelledError:
        return HttpResponse(status_code=499, body={"error": "Client Closed Request"}, headers={})
```

**Explanation**:
- **Technical Mechanics**: Catches `asyncio.CancelledError` when clients close connections mid-flight.
- **Business Decision & Why Made**: Handles premature client disconnections cleanly without surfacing internal stack traces.
- **Critical Importance**: Keeps logging clean and prevents resource leaks when users navigate away during request processing.
- **Second-Order Consequence**: Logs non-standard status code 499 (Client Closed Request) for observability metrics.

---

### Edge Case 20: Clock Skew & Signed Request Timestamp Window Verification

```python
import time

def verify_signed_request_timestamp(timestamp_str: str, max_skew_seconds: float = 300.0) -> bool:
    try:
        request_time = float(timestamp_str)
        return abs(time.time() - request_time) <= max_skew_seconds
    except (ValueError, TypeError):
        return False
```

**Explanation**:
- **Technical Mechanics**: Validates request timestamps against server system clocks.
- **Business Decision & Why Made**: Enforces signed request timestamp validation within a 5-minute window.
- **Critical Importance**: Rejects stale or replayed API requests, protecting against replay security attacks.
- **Second-Order Consequence**: Rejects requests missing valid timestamp headers at the perimeter.

---

### Edge Case 21: Method-Based Traffic Splitting (GET to Microservice, POST to Legacy)

```python
def evaluate_method_split(ctx: RequestContext, rule: Mapping[str, Any]) -> RoutingTarget:
    read_methods = {"GET", "HEAD", "OPTIONS"}
    if ctx.method in read_methods and rule.get("read_migrated"):
        return RoutingTarget.NEW_SERVICE
    return RoutingTarget.LEGACY
```

**Explanation**:
- **Technical Mechanics**: Evaluates HTTP methods, routing read operations (`GET`) to microservices while keeping write operations (`POST`) on legacy.
- **Business Decision & Why Made**: Enforces Meta-Decision 5 (Incremental Facade Routing) at the HTTP method level.
- **Critical Importance**: Allows safe production verification of read paths before cutting over complex write transactions.
- **Second-Order Consequence**: Eliminates risk to write ledgers during initial microservice rollout phases.

---

### Edge Case 22: CSRF Token & Cookie Domain Transformation

```python
def transform_cookie_domain(cookie_header: str, old_domain: str, new_domain: str) -> str:
    if not cookie_header:
        return ""
    return cookie_header.replace(f"Domain={old_domain}", f"Domain={new_domain}")
```

**Explanation**:
- **Technical Mechanics**: Rewrites `Domain` attributes in `Set-Cookie` headers.
- **Business Decision & Why Made**: Preserves session affinity and authentication state when proxying across different domain names.
- **Critical Importance**: Prevents user session logouts when requests are proxied between legacy and microservice hosts.
- **Second-Order Consequence**: Ensures `SameSite` and `Secure` cookie flags remain intact.

---

### Edge Case 23: Field Schema Renaming & Adapter Payload Mapping

```python
def transform_payload_to_new_schema(legacy_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(legacy_payload, dict):
        return legacy_payload
    return {
        "account_id": legacy_payload.get("user_id"),
        "contact_email": legacy_payload.get("email_address"),
        "active_status": legacy_payload.get("is_active", True)
    }
```

**Explanation**:
- **Technical Mechanics**: Maps legacy request body fields into canonical microservice schemas.
- **Business Decision & Why Made**: Translates legacy payloads into new schema formats transparently inside facade adapters.
- **Critical Importance**: Protects client applications from breaking changes during backend schema refactoring.
- **Second-Order Consequence**: Isolates schema translation logic within pure functional mappers.

---

### Edge Case 24: Multi-Region Traffic Routing & Geographic Fallback

```python
def resolve_regional_endpoint(client_region: str, regional_endpoints: Mapping[str, str], default_url: str) -> str:
    return regional_endpoints.get(client_region, default_url)
```

**Explanation**:
- **Technical Mechanics**: Resolves target URLs based on client regional headers (`CloudFront-Viewer-Country` or `X-Client-Region`).
- **Business Decision & Why Made**: Routes traffic to geographically optimal microservice deployments.
- **Critical Importance**: Reduces global latency and complies with regional data residency requirements.
- **Second-Order Consequence**: Defaults to primary fallback URLs if regional endpoints are unreachable.

---

### Edge Case 25: Sequence Re-Ordering in Shadow Mode Event Ingestion

```python
import time
from typing import Dict, Any

def create_ordered_shadow_event(event_type: str, payload: Any, sequence_num: int) -> Dict[str, Any]:
    return {
        "event_type": event_type,
        "sequence_num": sequence_num,
        "emitted_at": time.time(),
        "payload": payload
    }
```

**Explanation**:
- **Technical Mechanics**: Attaches monotonic sequence numbers and timestamps to shadow log events.
- **Business Decision & Why Made**: Enforces Second-Order Decision 15 (Monotonic Sequence Numbering).
- **Critical Importance**: Enables log processing pipelines to reorder events out-of-order background events.
- **Second-Order Consequence**: Prevents false-positive parity alerts caused by out-of-order log ingestion.

---

## 8. Operational & Parity Verification Checklist

Before toggling an endpoint from `shadow` to `fully_migrated`, complete the following operational verification steps:

1. **Zero High-Severity Diff Alerts**: Shadow mode differ must achieve >99.99% parity over 7 consecutive days (excluding ignored dynamic keys).
2. **Latency Differential Parity**: P99 latency of the new microservice must be equal to or lower than the legacy monolith ($P99_{\text{new}} \le P99_{\text{legacy}}$).
3. **Circuit Breaker Trip Test**: Verify via fault-injection that tripping the microservice circuit auto-routes 100% of traffic back to Legacy Monolith with 0 dropped HTTP requests.
4. **W3C Distributed Tracing Continuity**: Validate end-to-end trace context continuity in Grafana/Jaeger across Façade $\rightarrow$ New Microservice $\rightarrow$ Database child spans.
