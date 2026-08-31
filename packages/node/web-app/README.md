# Web App Package (`@observability/web-app`)

The frontend web application for the LLM Observability Platform, built with Next.js 15, React 19, TypeScript, Redux Toolkit/Saga, and OpenTelemetry Distributed Tracing.

---

## Available Commands

Run all commands from within the `packages/node/web-app` directory (or use `npm --prefix packages/node/web-app <command>` from the root).

### Development & Build
| Command | Description |
| :--- | :--- |
| `npm run dev` | Automatically frees ports `31400` & `31406`, clears `.next` cache, and launches Next.js (`http://localhost:31400`), Auth service, and Storybook (`http://localhost:31406`) concurrently |
| `npm run latency` / `npm run latency-engine` | Launches the Python Latency Engine worker service and REST query API (`http://localhost:8003`) |
| `npm run dev:latency` | Launches Next.js (`http://localhost:31400`) and Latency Engine (`http://localhost:8003`) concurrently |
| `npm run dev:all` | Launches Next.js (`http://localhost:31400`), Auth service (`http://localhost:3001`), Storybook (`http://localhost:31406`), and Latency Engine (`http://localhost:8003`) concurrently |
| `npm run clean` | Removes the `.next` cache directory |
| `npm run free-ports` | Kills any processes currently bound to registered service ports (`31400`, `3001`, `31406`, `8003`) |
| `npm run build` | Compiles and builds production bundle |
| `npm run start` | Starts production server on port `31400` after build |

### Linting & Type Checking
| Command | Description |
| :--- | :--- |
| `npm run lint` | Runs ESLint checks against strict type-safety, async safety, and complexity rules |
| `npx tsc --noEmit` | Runs strict TypeScript type checking without emitting files |

### Testing & Storybook
| Command | Description |
| :--- | :--- |
| `npm run test` | Runs unit and component tests using Vitest |
| `npm run storybook` | Starts Storybook dev environment at http://localhost:31406 |
| `npm run build-storybook` | Builds static Storybook documentation |

---

## Backend Requirements & API Contracts

The frontend features (`latency`, `quality`, `overview`, `traces`, `costs`) communicate with the backend query engine services via Next.js API Proxy routes.

### 1. Authentication & Security Header Requirement
- **JWT Authorization**: Outgoing service-to-service requests carry HMAC HS256 signed JWT tokens:
  ```http
  Authorization: Bearer <base64Url(header)>.<base64Url(payload)>.<base64Url(signature)>
  ```
  - **Required Claims**: `sub` (e.g. `web-app-quality-service`), `iat` (issued at epoch seconds), `exp` (expiration epoch seconds).
  - **Environment Key**: `JWT_SECRET` (defaults to development secret key).

### 2. OpenTelemetry & Distributed Context Propagation
- **Headers**: Every adapter request automatically propagates W3C context headers via `@observability/shared-infra`:
  - `traceparent`: `00-<trace_id>-<span_id>-01`
  - `x-trace-id`: `<32_hex_trace_id>`
  - `x-request-id`, `x-correlation-id`, `x-tenant-id`

### 3. Feature Endpoint Contracts

| Feature Slice | Next.js API Route | Backend Query Target | Response Payload Contract |
| :--- | :--- | :--- | :--- |
| **Latency** | `/api/v1/latency/percentiles` | `GET /v1/latency/percentiles` | `{ p50: number, p95: number, p99: number, sample_count: number }` |
| **Latency** | `/api/v1/latency/slo` | `GET /v1/latency/slo` | `{ burn_fast: number, burn_medium: number, burn_slow: number, budget_remaining_pct: number, slo_threshold_ms: number }` |
| **Latency** | `/api/v1/latency/attribution` | `GET /v1/latency/attribution` | `{ dns: number, tcp: number, queue: number, inference: number }` |
| **Latency** | `/api/v1/latency/baseline` | `GET /v1/latency/baseline` | Array of `{ date: string, p99_ttft_ms: number, p99_total_ms: number }` |
| **Quality** | `/api/v1/quality/summary` | `GET /v1/quality/summary` | `{ avg_quality_score: number, score_delta_pct: number, below_slo_count: number, total_evaluated_prompts: number }` |
| **Quality** | `/api/v1/quality/trend` | `GET /v1/quality/trend` | Array of `{ date: string, avg_quality_score: number, toxicity_alerts: number, hallucination_alerts: number }` |
| **Quality** | `/api/v1/quality/models` | `GET /v1/quality/models` | Array of `{ model: string, avg_score: number, min_score: number, max_score: number, evaluation_count: number, pass_rate_pct: number }` |
| **Quality** | `/api/v1/quality/flagged` | `GET /v1/quality/flagged` | Array of `{ id: string, span_id: string, alert_type: string, severity: string, confidence_score: number, prompt_snippet: string, timestamp: string }` |
| **Overview** | `/api/v1/overview/summary` | `GET /v1/overview/summary` | `{ p95_latency_ms: number, quality_avg_score: number, total_spend_usd: number, active_spans_count: number, p95_latency_delta_pct: number, quality_delta_pct: number, spend_delta_pct: number }` |
| **Overview** | `/api/v1/overview/health` | `GET /v1/overview/health` | `{ status: string, fast_burn_active: boolean, medium_burn_active: boolean, active_alerts_count: number, message: string }` |
| **Traces** | `/api/v1/traces/list` | `GET /v1/traces/list` | Array of `{ id: string, root_span_name: string, service: string, model: string, duration_ms: number, total_tokens: number, cost_usd: number, status: string, timestamp: string }` |
| **Traces** | `/api/v1/traces/[traceId]` | `GET /v1/traces/:traceId` | `{ trace_id: string, root_span_name: string, total_duration_ms: number, spans: Array<SpanNode> }` |
| **Costs** | `/api/v1/costs/summary` | `GET /v1/costs/summary` | `{ total_cost_usd: number, daily_avg_usd: number, cost_delta_pct: number, projected_monthly_usd: number }` |
| **Costs** | `/api/v1/costs/providers` | `GET /v1/costs/providers` | Array of `{ provider: string, model: string, cost_usd: number, token_count: number, pct_of_total: number }` |

---

## OpenTelemetry Distributed Tracing & Middleware Architecture

1. **Centralized Tracing Initialization (`src/core/tracing/tracer.ts`)**:
   - Client-side: `WebTracerProvider` with `BatchSpanProcessor(OTLPTraceExporter)` pushing OTLP traces directly to OpenTelemetry Collector (`http://localhost:31417/v1/traces`).
   - Server-side: Dynamically loads `@observability/shared-infra/tracing` Node.js OpenTelemetry provider for React Server Components (RSC) and Server Side Rendering (SSR).

2. **Next.js W3C Context Propagation (`src/middleware.ts`)**:
   - Next.js middleware extracts or generates W3C `traceparent`, `x-request-id`, `x-correlation-id`, and `tracestate` headers.
   - Sets context headers on both internal request (`NextResponse.next({ request: { headers } })`) and outgoing HTTP response pipelines.

3. **Grafana Tempo TraceQL Queries**:
   - Query by service name: `{ resource.service.name = "web-app" }`
   - Query by endpoint: `{ resource.service.name = "web-app" && name = "HTTP GET /costs" }`
   - Query by Trace ID: Switch query mode to **Trace ID** in Grafana Explore (`http://localhost:31415/explore`) and paste the 32-character hex trace ID from the `traceparent` response header.

---

## Production Next.js + TypeScript Standard Enforced

### 1. Strict Type Safety
- **No `any`**: `any` is prohibited (`@typescript-eslint/no-explicit-any`).
- **No Unsafe Type Assertions**: Restricted via `@typescript-eslint/consistent-type-assertions`.
- **No Non-Null Assertions**: Prohibited `!` (`@typescript-eslint/no-non-null-assertion`).
- **Type Checking Flags**: `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `noUncheckedIndexedAccess`.

### 2. Async & Promise Safety
- **Never Ignore Promises**: Enforced `@typescript-eslint/no-floating-promises`.
- **Async Callbacks & Failures**: Enforced `@typescript-eslint/no-misused-promises`.

### 3. Complexity & Limits
- **Cyclomatic Complexity**: Max **10** (`complexity`).
- **Function Length**: Warning at **50** lines (`max-lines-per-function`).
- **Maximum Parameters**: Max **4** (`max-params`).
- **Maximum Nesting Depth**: Max **3** (`max-depth`).

### 4. Control Flow & Code Quality
- **Exhaustive State Handling**: `default-case`, `default-case-last`, `no-fallthrough`.
- **Strict Equality**: Enforced `eqeqeq` (`===` and `!==` only).
- **Unused Variables**: Enforced `@typescript-eslint/no-unused-vars`.
