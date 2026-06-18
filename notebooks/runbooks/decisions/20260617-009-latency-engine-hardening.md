# ADR-009 — Latency Engine Hardening, Containerization, OTel Tracing, and CI Pipeline

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 009                                                               |
| **Date**    | 2026-06-17                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/latency-engine`                                  |

---

## Context

To bring the newly designed `latency-engine` to production-readiness, we needed to deliver:
1. **Containerization & Common Networking:** Create a multi-stage Dockerfile and a docker-compose deployment configuration integrating the service with shared Redis and Redpanda message brokers on a common `llm_obs_network`.
2. **In-Depth Tracing:** Implement native OpenTelemetry tracing, with trace propagation over Kafka headers to context-link downstream aggregations with original client spans, and record sub-millisecond network/inference latency attributes.
3. **Pluggable Architecture:** Expose public interfaces (`LatencyHandler`, configs) at the package initialization level to enable other services to import and plug the latency engine into their own pipelines.
4. **Validation & CI Automation:** Write event contracts (AsyncAPI standard), validation scripts, and a lightweight GitHub Actions workflow to run checks and tests automatically on push/merge to the `main` branch.

---

## Decision

We implemented the following design choices:

- **logarithmic DDSketch Mapper:** Configured DDSketch with a target relative accuracy of $\epsilon = 0.01$ (1% error bound). Real-valued latencies are mapped to logarithmic buckets, allowing high-precision quantile (p50, p95, p99) estimations.
- **Base64 Protobuf Redis Serialization:** DDSketches are serialized using Google Protocol Buffers (`ddsketch.pb.proto`) and encoded in Base64 strings before storage in Redis, minimizing key sizes to $< 500$ bytes.
- **Bridge Network Topology:** Built a shared Docker network `llm_obs_network` in `docker-compose.yaml` to unify cross-container resolution between workers.
- **Extract-and-Propagate Tracing Adapter:** Embedded OpenTelemetry trace parent parsing within `index.py` using standard `TraceContextTextMapPropagator`. Spans created during `LatencyHandler.handle_spans` are parent-linked to these extracted contexts.
- **Contract Validator Hook:** Added a pre-flight regex validator validating local schemas against standard AsyncAPI formats prior to test execution.

---

## Failure-First System Building (FFSB) Analysis

### Mode 1: Redis Outage (Network Refusal)
- **Symptom**: Worker crashes or stalls Kafka polling when Redis becomes unavailable.
- **Prevention**: Implemented a localized memory queue buffer in `LatencyHandler`. When Redis fails, DDSketch updates are buffered in memory up to a capacity of 1000 items. If capacity is exceeded, oldest metrics are dropped, logging the `latency_sketch_dropped_total` count. The worker commits Kafka offsets normally to prevent queue lag. Upon Redis recovery, the buffer is replayed and cleared.

### Mode 2: Multi-Container Host Port Collisions
- **Symptom**: Port `8002` (healthcheck) or Kafka `9092` conflicts with existing running services.
- **Prevention**: Configured `HEALTH_PORT` and other endpoints to fallback to standard configurable environment variables, and bridged all communication inside an isolated virtual network `llm_obs_network`.

### Mode 3: OTel Package Missing / Exporter Bottlenecks
- **Symptom**: Missing OpenTelemetry packages crash the process or HTTP/gRPC exporter calls block hot-path loops.
- **Prevention**: Wrapped OTLPSpanExporter imports in `try-except` clauses (falls back to console logging when OTLP is missing) and wrapped individual span creation blockages safely.

---

## Consequences

### Positive
- **Guaranteed Percentile Bounds:** Limits maximum estimation error to 1% while eliminating the need to store raw float arrays.
- **Pluggable SDK Capability:** Other services can easily import `LatencyHandler` directly from the `latency-engine` module.
- **End-to-End Tracing:** Resolves latency bottlenecks instantly by visualizing network DNS/TCP, queue, and inference time attributes.

### Negative / Trade-offs
- **DDSketch Protobuf Dependencies:** Requires additional runtime packages (`protobuf`, `ddsketch`) in the environment.
- **In-Memory Buffering:** Running with buffered metrics during Redis outages risks losing unwritten data if the worker container itself crashes before recovery.
