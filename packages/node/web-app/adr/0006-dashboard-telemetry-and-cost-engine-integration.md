# ADR 0006: Web App Dashboard Integration with Telemetry SDK and Event Cost Engine

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-NODE-WEB-APP-0006` |
| **Title** | Web App Dashboard Integration with Python Telemetry SDK and Event Cost Engine |
| **Status** | **Accepted** |
| **Date** | 2026-08-25 |
| **Scope** | Next.js Web App (`packages/node/web-app`), Telemetry SDK (`instrumentation-sdk`), Cost Engine (`event-cost`) |

---

## 1. Context & Problem Statement

The `web-app` microservice provides the primary user-facing Next.js dashboard (`/costs`, `/traces`, `/latency`, `/quality`, `/prompts`). To render real-time observability metrics, cost breakdowns, and distributed trace waterfalls, `web-app` must interface cleanly with the Python backend services:
- **`instrumentation-sdk`**: Captures raw LLM spans, token counts, TTFT, PII flags, and exposes REST management APIs.
- **`event-cost`**: Computes micro-USD LLM costs and manages pricing registries (`model_prices.yaml`).
- **`event-cost-worker`**: Consumes raw spans from Kafka and persists aggregated analytics to PostgreSQL/ClickHouse.

We need a formal High-Level Design (HLD) and Low-Level Design (LLD) detailing how `web-app` connects to these backend components reliably.

---

## 2. High-Level Design (HLD)

### 2.1 High-Level Architecture Topology

```mermaid
flowchart TD
    subgraph AppLayer["Application & Capture Layer"]
        UserApp["Python / Node LLM App"]
        SDK["packages/python/instrumentation-sdk\n(Span Capture, PII Scanning, TTFT)"]
        UserApp --> SDK
    end

    subgraph ProcessingStorage["Processing & Storage Layer"]
        CostEngine["packages/python/event-cost\n(Micro-USD Cost Computation)"]
        CostWorker["event-cost-worker\n(Kafka Consumer & Aggregator)"]
        AnalyticsDB[("PostgreSQL / ClickHouse / Redis\n(Spans, Traces, Cost Ledgers)")]

        SDK --> CostEngine
        SDK -->|Kafka: llm.spans.raw or REST POST /v1/spans| CostWorker
        CostWorker --> AnalyticsDB
        SDK -->|FastAPI REST Server :8000| AnalyticsDB
    end

    subgraph FrontendLayer["Next.js Web App Dashboard Layer"]
        WebApp["packages/node/web-app\n(Next.js App Router on :3000)"]
        DashboardRoutes["/costs | /traces | /latency | /prompts"]
        
        WebApp --> DashboardRoutes
        WebApp -->|Pattern A: REST API Fetch| SDK
        WebApp -->|Pattern B: Server Route DB Queries| AnalyticsDB
        WebApp -->|Pattern C: OTLP Web Tracing| AnalyticsDB
    end
```

### 2.3 Three-Plane Architectural Blueprint (Control, Data & Messaging)

```mermaid
flowchart TD
    subgraph ControlPlane["1. CONTROL PLANE (Configuration & Policy Governance)"]
        ConfigState["Dashboard Filter State (useDashboardFilters)"]
        PriceReloadSignal["Hot-Reload Price Signal (POST /v1/metrics/prices/reload)"]
        TenantAuth["Auth Context & API Keys (x-api-key)"]
    end

    subgraph DataPlane["2. DATA PLANE (High-Throughput Analytics & Rendering)"]
        WebAppUI["Next.js React Dashboard UI (Pages & Suspense Views)"]
        ServerActions["Next.js Server API Routes / Direct DB Query"]
        RestProxy["FastAPI REST Ingestion Proxy (http://localhost:8000)"]
        AnalyticsStore[("PostgreSQL / ClickHouse Analytics Store")]

        WebAppUI --> ServerActions
        ServerActions --> AnalyticsStore
        WebAppUI --> RestProxy
    end

    subgraph MessagingPlane["3. MESSAGING PLANE (Asynchronous Telemetry & Tracing)"]
        OtelExporter["OTLP Web SDK Exporter (NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT)"]
        TempoCollector["OpenTelemetry Collector & Tempo Tracing Engine (Port 31417)"]
        SseStreamer["Server-Sent Events (SSE) / Real-time WebSockets"]

        WebAppUI --> OtelExporter
        OtelExporter --> TempoCollector
        RestProxy --> SseStreamer
        SseStreamer --> WebAppUI
    end

    ControlPlane --> DataPlane
    MessagingPlane --> DataPlane
```

### 2.4 Integration Architectural Patterns

| Pattern | Description | Primary Use Case | Target Endpoint |
|---|---|---|---|
| **Pattern A: REST API Proxy** | Next.js Client/Server Components fetch directly from `instrumentation-sdk` REST API | Dynamic pricing lists, test LLM calls, span ingestion status | `http://localhost:8000/v1/metrics/prices`<br>`http://localhost:8000/v1/spans` |
| **Pattern B: Direct DB Analytics** | Next.js Server Actions / API Routes query PostgreSQL or ClickHouse ledgers | Heavy dashboard aggregations (`SUM(cost_usd_micro)`, `p95` latencies) | `postgresql://admin:password@localhost:5432/llm_observability` |
| **Pattern C: OTLP Web Tracing** | Next.js frontend emits OpenTelemetry traces via OTLP Exporter | End-to-end user navigation trace context propagation | `http://localhost:31417/v1/traces` |

---

## 3. Low-Level Design (LLD)

### 3.1 Sequence Diagram: Web App Data Fetching & Tracing Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Dashboard User
    participant WebApp as Next.js Web App (3000)
    participant NextApi as Next.js Server API Route
    participant RestApi as instrumentation-sdk API (8000)
    participant AnalyticsDB as Analytics Store (Postgres/Redis)

    Note over User, AnalyticsDB: Phase 1: Cost Dashboard Initial Load
    User->>WebApp: Navigate to /costs
    activate WebApp
    WebApp->>NextApi: GET /api/costs?timeRange=24h&model=gpt-4o
    activate NextApi

    par Fetch Real-Time Model Prices
        NextApi->>RestApi: GET /v1/metrics/prices
        RestApi-->>NextApi: List[ModelPriceDTO] (gpt-4o, claude-3)
    and Fetch Aggregated Ledger Spend
        NextApi->>AnalyticsDB: SELECT SUM(cost_usd_micro) GROUP BY provider, model
        AnalyticsDB-->>NextApi: CostAggregatesResultSet
    end

    NextApi-->>WebApp: JSON Response (Total spend, breakdown by model/provider)
    deactivate NextApi
    WebApp-->>User: Render Cost Analytics Cards & Charts
    deactivate WebApp

    Note over User, AnalyticsDB: Phase 2: Live Trace Detail Inspection
    User->>WebApp: Click Trace ID (e.g. "tr-98421")
    activate WebApp
    WebApp->>RestApi: POST /v1/spans (Query trace_id="tr-98421")
    RestApi->>AnalyticsDB: Query span tree & TTFT metrics
    AnalyticsDB-->>RestApi: SpanRecordTree
    RestApi-->>WebApp: Detailed Span Payload (tokens, latency, PII flags)
    WebApp-->>User: Render Interactive Trace Waterfall & Cost Breakdown
    deactivate WebApp
```

### 3.2 Component Contracts & Environment Configurations

#### Environment Variables (`packages/node/web-app/.env.local`)
```env
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
DATABASE_URL="postgresql://admin:password@localhost:5432/llm_observability"
NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:31417/v1/traces"
```

#### TypeScript API Client Contract (`packages/node/web-app/src/lib/telemetry-client.ts`)
```typescript
export interface ModelPrice {
  model: string;
  provider: string;
  input_price_per_1m: number;
  output_price_per_1m: number;
  version: string;
}

export interface CostSummaryResponse {
  total_spend_usd: number;
  currency: string;
  time_range: string;
  breakdown: Array<{
    provider: string;
    model: string;
    cost_usd: number;
    tokens_count: number;
  }>;
}

export async function getModelPrices(): Promise<ModelPrice[]> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const res = await fetch(`${baseUrl}/v1/metrics/prices`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error('Failed to fetch model prices');
  return res.json();
}
```

---

## 4. End-to-End Call Stack Topology

```text
└── [User Navigation] User opens http://localhost:3000/costs
    ├── 1. app/(dashboard)/costs/page.tsx :: CostDashboardPage()
    │   └── 2. React.Suspense :: Fallback pulse skeleton
    │       └── 3. page.tsx :: CostDashboardContent()
    │           ├── 4. hooks/useDashboardFilters.ts :: useDashboardFilters()
    │           │   └── Extract searchParams (`timeRange`, `model`, `service`, `environment`)
    │           ├── 5. components/forms/DashboardFilterBar.tsx :: DashboardFilterBar()
    │           └── 6. lib/telemetry-client.ts :: fetchModelPrices()
    │               └── HTTP GET http://localhost:8000/v1/metrics/prices
    │                   ├── 7. FastAPI :: router.get("/v1/metrics/prices")
    │                   └── 8. price_registry.py :: get_all_prices()
    │
    └── [Trace Waterfall Inspection] Click Trace ID "tr-98421"
        ├── 1. app/(dashboard)/traces/page.tsx :: TraceDetailsModal()
        └── 2. lib/telemetry-client.ts :: fetchTraceSpans("tr-98421")
            └── HTTP POST http://localhost:8000/v1/spans (Query trace_id)
                ├── 3. spans/service.py :: query_span_tree("tr-98421")
                ├── 4. postgres/adapter.py :: SELECT * FROM llm_spans WHERE trace_id = 'tr-98421'
                └── 5. components/views/TraceWaterfall.tsx :: Render Interactive Gantt Chart
```

---

## 5. Decision Rationale & Consequences

### Positive Consequences
- **Decoupled Architecture**: `web-app` consumes standardized REST & OTLP endpoints without tight coupling to Python worker implementations.
- **High Performance**: Heavy aggregation runs asynchronously via `event-cost-worker` into PostgreSQL/ClickHouse, allowing Next.js Server Components to render dashboards with sub-100ms response times.
- **Fail-Safe Operation**: If the REST API is temporarily unavailable, Next.js Server Actions can fall back to cached pricing data or direct database reads.

### Negative Consequences
- Requires maintaining database schemas and API contract DTOs across Python (`api-types`) and TypeScript packages.
