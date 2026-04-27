# Log Intelligence Pipeline (Draft v0)

This document captures the first implementation pass for a layered log intelligence pipeline in `infrastructure/observability/server/log_intelligence_pipeline.py`.

## Proposed folder structure (ASCII)

```text
infrastructure/
└── observability/
    ├── LOG_INTELLIGENCE_ARCHITECTURE.md
    ├── server/
    │   ├── __init__.py
    │   ├── log_intelligence_pipeline.py
    │   ├── ingestion/
    │   │   ├── drain3_parser.py
    │   │   ├── template_store.py
    │   │   └── log_receiver.py
    │   ├── enrichment/
    │   │   ├── structural_enricher.py
    │   │   ├── semantic_embedder.py
    │   │   └── anomaly_scorer.py
    │   ├── intelligence/
    │   │   ├── count_min_sketch.py
    │   │   ├── drift_detector.py
    │   │   ├── semantic_index.py
    │   │   └── trace_index.py
    │   ├── storage/
    │   │   ├── router.py
    │   │   ├── hot_loki.py
    │   │   ├── warm_clickhouse.py
    │   │   └── cold_parquet_s3.py
    │   └── api/
    │       ├── ingest_api.py
    │       └── query_api.py
    └── test/
        ├── unit/
        │   ├── test_ingestion.py
        │   ├── test_enrichment.py
        │   ├── test_intelligence.py
        │   └── test_storage_router.py
        ├── integration/
        │   └── test_pipeline_e2e.py
        └── e2e/
            └── test_loki_clickhouse_s3_flow.py
```

## Decision tree (ASCII)

```text
[Incoming log line]
        |
        v
[Parse with Drain3-like parser]
        |
        +--> Parse failed?
        |       |
        |       +--> YES: assign template_id="unknown" + store raw + mark anomaly=1.0
        |       |
        |       +--> NO: continue
        v
[Template lookup/create]
        |
        v
[Parallel enrichment]
   /           |            \
  v            v             v
[Structural] [Semantic]   [Anomaly inputs]
  |            |             |
  |            +--> embedding cached?
  |                    |
  |                    +--> YES: reuse cached vector
  |                    |
  |                    +--> NO: compute embedding + cache
  |
  +--> missing key fields (timestamp/level/service)?
          |
          +--> YES: add defaults + quality_flag="partial"
          |
          +--> NO: quality_flag="complete"

[Frequency + drift checks]
        |
        +--> drift detected?
        |       |
        |       +--> YES: boost anomaly score + emit drift alert
        |       |
        |       +--> NO: keep baseline anomaly score
        v
[Persist by time horizon]
        |
        +--> <=24h ---------> [Hot: Loki]
        |
        +--> <=30d ---------> [Warm: ClickHouse]
        |
        +--> >30d ----------> [Cold: Parquet/S3]
        v
[Index updates]
   |- semantic ANN index (template similarity)
   |- trace_id inverted index (trace context)
   |- template frequency sketch
        |
        v
[Query/read path]
        |
        +--> "similar logs"? -----> ANN search
        |
        +--> "trace context"? ----> trace_id lookup
        |
        +--> "time-range query"? -> tier router + federated merge
```

## Layer mapping

### 1) Ingestion layer
- `Drain3LikeParser` normalizes dynamic tokens and produces a stable `template_id`.
- `TemplateStore` keeps template text keyed by `template_id`.
- `LogIntelligencePipeline.ingest` performs O(1)-style in-memory path for each log line.

### 2) Enrichment layer
- **Path A (structural):** `StructuralEnricher` extracts timestamp, level, service, trace_id and normalizes ISO8601 and log-level values.
- **Path B (semantic):** `TemplateEmbeddingCache` provides 384-dimensional deterministic vectors and caches per `template_id`.
- **Path C (anomaly):** `IsolationForestLikeScorer` computes a bounded anomaly score `[0,1]` from frequency, field novelty, and drift indicators.

### 3) Intelligence layer
- `CountMinSketch(width=2000, depth=7)` tracks template frequency with fixed memory profile.
- `ADWINLikeDriftDetector(max_window=50)` flags abrupt template frequency shifts.
- `HNSWLikeIndex` stores embeddings and supports nearest-neighbor retrieval APIs.
- `TraceInvertedIndex` links `trace_id` to log line ids.

### 4) Storage layer (next phase)
Current implementation is in-memory only. Planned production storage routing:
- hot: Loki
- warm: ClickHouse
- cold: Parquet on S3

## Current status

Implemented in this iteration:
- End-to-end ingestion API from raw line to parsed+enriched log record.
- Templateization, normalization, frequency sketch, drift checks, anomaly scoring.
- Semantic index insert + similarity lookup.
- Trace-level reverse index for fast context fetch.

Pending work for production readiness:
- Replace deterministic embedding stub with MiniLM-L6 inference service and GPU batch path.
- Replace heuristic anomaly scorer with trained Isolation Forest model lifecycle.
- Add persistent tiered storage adapters and federated query router.
- Add real HNSW backend integration and configurable ANN parameters.
- Add precision/recall and throughput benchmark suite.

## Planned architecture vs delivered status (as of 2026-04-27)

### Ingestion layer
- Raw multi-service log ingestion path: **partial** (implemented in-memory ingest API; external stream adapters pending).
- Drain3 online parsing behavior: **partial** (Drain3-like normalization parser implemented; full Drain3 parse-tree algorithm integration pending).
- Template store: **implemented** (trie-backed lookup + template_id mapping).

### Enrichment layer
- Structural extraction and normalization: **implemented**.
- Semantic embedding with MiniLM-L6 and GPU batching: **partial** (MiniLM-L6 adapter with fallback cache implemented; dedicated GPU batching service pending).
- Isolation Forest anomaly scoring: **partial** (runtime Isolation Forest scorer implemented; offline model lifecycle and calibration pipeline pending).

### Intelligence layer
- Count-Min Sketch width=2000/depth=7: **implemented**.
- ADWIN-based drift detection: **partial** (ADWIN-like detector implemented; true ADWIN algorithm integration pending).
- HNSW semantic search: **partial** (nearest-neighbor semantic index implemented; true HNSW backend with ef/M tuning pending).
- Trace inverted index: **implemented**.

### Storage layer
- Hot/Warm/Cold tier decision routing: **implemented** (logical router only).
- Loki/ClickHouse/S3 persistence adapters: **not implemented**.
- Federated query merging: **not implemented**.
- Compression pipeline (template + deltas + zstd): **not implemented**.

### Accuracy and SLO claims
- Claimed accuracy/recall/precision values from the target design are **not yet validated** in this codebase.
- Benchmark and validation suite remains **pending**.

### Practical conclusion
Current delivery is a strong scaffold with working contracts and tests, but it does **not** yet fully achieve the production-level architecture and metrics listed in the original plan.
