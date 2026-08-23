# ADR 0005: Deep-Linkable URL Filter Pipeline Engine & OpenTelemetry Web SDK Tracing

- **Status**: Accepted
- **Date**: 2026-08-23
- **Authors**: Web Architecture Team
- **Feature**: F-11 (Deep-Linkable URL Filters & Observability Tracing)

---

## Context & Problem Statement

Observability dashboards (`/costs`, `/latency`, `/quality`, `/prompts`, `/traces`) require real-time state synchronization with URL query parameters (`timeRange`, `from`, `to`, `model`, `service`, `environment`) to support deep-linking, bookmarking, and team collaboration.

Prior implementations suffered from imperative loops, duplicated state handling across components, and lack of OpenTelemetry span propagation during client-side filter transformations.

---

## Decision Drivers

1. **Pure Data-Driven Architecture**: Declarative filter rules table separate from evaluation engine logic.
2. **Functional Pipeline (Zero Loops)**: Use `reduce` (fold), `map`, and `filter` array transformations instead of imperative loops.
3. **OpenTelemetry Web SDK Integration**: Automatically emit active spans with modern semantic conventions (`ATTR_SERVICE_NAME`, `ATTR_SERVICE_VERSION`) via `BatchSpanProcessor` and `OTLPTraceExporter` to `http://localhost:31417/v1/traces` (Grafana Tempo).
4. **CORS & Preflight Compliance**: OpenTelemetry Collector configured with `cors.allowed_origins` to allow cross-origin span ingestion from Next.js dashboard origins (`http://localhost:31400`).
5. **Next.js 15 RSC & Suspense Safety**: Wrap `useSearchParams()` consumption inside `<Suspense>` boundaries to ensure server-side rendering (RSC) and client navigation stability.

---

## Architectural Diagrams

### High-Level Architecture Diagram

```mermaid
graph TD
    Browser["Next.js Browser Client (Port 31400)"] -->|"URL Query Params (/costs?timeRange=7d&model=gpt-4o)"| Hook["useDashboardFilters Hook"]
    Hook -->|"Declarative Rules"| Pipeline["executeFilterPipeline Engine"]
    Pipeline -->|"Functional Fold"| ListOps["ListOp Data Steps"]
    Pipeline -->|"Active Span"| OTEL["OpenTelemetry Web SDK"]
    OTEL -->|"BatchSpanProcessor (OTLP/HTTP Port 31417)"| Collector["frontend-otel-collector (Port 31417)"]
    Collector -->|"gRPC Spans (Port 3200)"| Tempo["frontend-tempo (Port 3200)"]
    Tempo -->|"TraceQL Query"| Grafana["Grafana Explore UI (Port 31415 / 31419)"]
    ListOps -->|"transformList()"| UI["DataTable / EmptyState View"]
```

### Low-Level Execution Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Router as Next.js Router
    participant Page as Dashboard Page (RSC + Suspense)
    participant Hook as useDashboardFilters
    participant Engine as filter-pipeline.engine
    participant OTEL as OpenTelemetry Web SDK
    participant Collector as OTEL Collector (OTLP/HTTP Port 31417)
    participant Tempo as Grafana Tempo (Port 3200)

    User->>Router: Select Filter / Load Deep-Link URL
    Router->>Page: Render Page Shell & Suspense Boundary
    Page->>Hook: Invoke useDashboardFilters()
    Hook->>Engine: executeFilterPipeline(searchParams)
    Engine->>OTEL: startActiveSpan("executeFilterPipeline")
    Engine->>Engine: FILTER_PIPELINE_RULES.reduce(fold)
    Engine->>OTEL: span.setAttribute("filter.model", "gpt-4o")
    Engine->>OTEL: span.end()
    OTEL->>Collector: OPTIONS Preflight & POST OTLP Trace Span (http://localhost:31417/v1/traces)
    Collector->>Tempo: Export gRPC Spans (Port 3200)
    Engine-->>Hook: Return { filters, listOps, trace }
    Hook-->>Page: Render FilterBar & Data Views
```

---

## End-to-End Function Call Stack (ASCII Tree)

```text
URL Query Param Update / Deep-Link Filter Execution Flow
└── User Selects Filter / Navigates to Deep Link (/costs?timeRange=7d&model=gpt-4o)
    └── Next.js App Router (RSC + Client Boundary) [page.tsx]
        └── <Suspense> Boundary Wrapper [page.tsx]
            └── DashboardContent Component [page.tsx]
                └── useDashboardFilters() Hook [useDashboardFilters.ts]
                    │
                    ├── 1. executeFilterPipeline(searchParams) [filter-pipeline.engine.ts]
                    │   ├── OpenTelemetry Tracer.startActiveSpan('executeFilterPipeline') [tracer.ts]
                    │   │   ├── ATTR_SERVICE_NAME: 'web-app' [tracer.ts]
                    │   │   └── ATTR_SERVICE_VERSION: '0.1.0' [tracer.ts]
                    │   │
                    │   ├── FILTER_PIPELINE_RULES.reduce(fold) [filter-pipeline.rules.ts]
                    │   │   ├── processFilterRule('timeRange') -> '7d'
                    │   │   ├── processFilterRule('model') -> 'gpt-4o'
                    │   │   ├── processFilterRule('service') -> 'checkout-service'
                    │   │   └── processFilterRule('environment') -> 'production'
                    │   │
                    │   └── span.end() -> exports FilterPipelineTraceSpan { traceId, durationMs }
                    │
                    ├── 2. buildFilterListOps(filters) [filter-pipeline.engine.ts]
                    │   └── Transforms filters into ListOp[] declarative data steps
                    │
                    ├── 3. transformList(rows, listOps) [core/data-driven/list-transform.ts]
                    │   └── Functional reduce fold filtering rows with zero imperative loops
                    │
                    └── 4. OTLPTraceExporter -> BatchSpanProcessor -> OTEL Collector (http://localhost:31417/v1/traces)
                        └── gRPC -> Tempo:3200 -> Queryable in Grafana Explore via TraceQL
```

---

## Consequences

### Positive
- **Deep-Linkable URL State**: Bookmarkable filter URLs across all dashboard pages.
- **Trace Observability**: End-to-end active span propagation into Grafana Tempo via port 31417.
- **CORS Compliant**: Preflight OPTIONS requests handled seamlessly across cross-origin ports.
- **Zero Imperative Loops**: Clean functional pipeline using `reduce`, `map`, and `filter`.
- **RSC Stability**: Wrapped in `<Suspense>` boundaries to ensure Next.js 15 streaming support.

### Negative
- Requires client-side hydration for URL search parameter processing.
