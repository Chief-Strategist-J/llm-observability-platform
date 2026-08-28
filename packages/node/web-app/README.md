# Web App Package (`@observability/web-app`)

The frontend web application for the LLM Observability Platform, built with Next.js 15, React 19, TypeScript, Redux Toolkit/Saga, and OpenTelemetry Distributed Tracing.

---

## Available Commands

Run all commands from within the `packages/node/web-app` directory (or use `npm --prefix packages/node/web-app <command>` from the root).

### Development & Build
| Command | Description |
| :--- | :--- |
| `npm run dev` | Automatically frees ports `31400` & `31406`, clears `.next` cache, and launches Next.js (`http://localhost:31400`) and Storybook (`http://localhost:31406`) concurrently |
| `npm run clean` | Removes the `.next` cache directory |
| `npm run free-ports` | Kills any processes currently bound to ports `31400` or `31406` |
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
