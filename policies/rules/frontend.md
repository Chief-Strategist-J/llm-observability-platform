# Frontend Rules & Core Tech Stack

## System Architecture Overview

**Core Design Philosophy:** Every component is built and reviewed in Storybook *before* it touches real data. Every data-bearing view has a server-rendered "cold" state (Next.js RSC hitting ClickHouse/PostgreSQL) and a "live" state (SSE/WebSocket via `packages/realtime-sdk`) — and a component renders identically regardless of which one fed it. Nothing fetches data directly; everything flows through one typed data layer, and no chart or table re-derives a sum, percentile, or cost figure that the backend already computed.

```
Browser
  ↓
Next.js App Router (RSC + Client Components)
  ↓
Typed Data Layer (tRPC client + TanStack Query cache)
  ↓                                        ↓
tRPC / OpenAPI (Layer 1-6 read + admin APIs)   packages/realtime-sdk (SSE cron/queue, WS events)
  ↓                                        ↓
PostgreSQL (OLTP) | ClickHouse (OLAP)         Kafka consumer bridge → WS/SSE fan-out
  ↓
Component Library (Storybook-verified) — renders cold and live state identically
```

## Core Tech Stack (Quick Reference)

| Domain | Technology | Why |
| --- | --- | --- |
| Language | TypeScript (strict mode) | Same contract discipline as the Span Schema — no `any` crossing an API boundary |
| Framework | Next.js 15 (App Router) | RSC for first paint on ClickHouse aggregates, streaming for slow queries, one deploy target |
| UI primitives | Radix UI + shadcn/ui | Unstyled, accessible primitives — we own the styling layer, not fight it |
| Styling | Tailwind CSS + CSS variables | Token-driven, matches Storybook workflow; dark/light/high-contrast via CSS vars, not duplicated components |
| Component workshop | Storybook 8 (Vite builder) | Every component built and reviewed in isolation before it's wired to data |
| Data fetching/cache | TanStack Query | Identical cache semantics for RSC-hydrated data and live SSE/WS deltas |
| API layer (internal) | tRPC | End-to-end type safety inside the monorepo |
| API layer (external) | Generated OpenAPI client | For enterprise (ICP-03) consumers who don't want a Next.js-coupled client |
| Real-time transport | `packages/realtime-sdk` | Reuses the backend's existing SSE/WS client wrapper — no second transport implementation |
| Charting (primitives) | visx | SVG, composable, good for small/static charts |
| Charting (high-frequency) | uPlot | Canvas-based; DDSketch bands and multi-thousand-point latency series need this, not SVG-per-point |
| State (client, non-server) | Zustand | Small, no boilerplate, kept strictly separate from server cache state |
| Forms | React Hook Form + Zod | Zod schemas shared with tRPC input validation — one schema, two consumers |
| Auth | Auth.js (NextAuth) | Org-aware session: carries org_id, role, feature-flag bundle |
| Testing (unit) | Vitest + React Testing Library | Fast, ESM-native, same config as the Vite-built Storybook |
| Testing (visual) | Storybook test-runner + Chromatic | Every PR gets a visual diff on the component library, not just the app shell |
| Testing (e2e) | Playwright | Cross-browser, run against preview deployments and staging |
| Monorepo tooling | Turborepo + pnpm workspaces | Frontend lives in `apps/web`, shares `packages/realtime-sdk`, `packages/design-tokens`, `packages/api-types` |
| Error/perf monitoring | Sentry + Web Vitals reporting | The frontend must be as self-observing as the backend SDK's health endpoint (F-23 parity) |
| Deployment | Vercel or self-hosted Node (Docker) | Two supported targets, both RSC/SSR-compatible |

---

## Data Flow (End-to-End)

1. Request hits Next.js App Router; RSC segment resolves org/session server-side via Auth.js
2. RSC calls a tRPC procedure → PostgreSQL (hot OLTP: budgets, alerts, configs) or ClickHouse (OLAP: cost/latency/quality aggregates), depending on the query
3. Server renders the "cold" state HTML with data embedded as the TanStack Query hydration payload
4. Client hydrates; TanStack Query takes cache ownership — no refetch on mount at the hydration boundary
5. Components needing live data open a subscription via `packages/realtime-sdk` (SSE for aggregate/cron-driven views, WS for per-event views like the live trace stream)
6. Incoming deltas are normalized by a typed reducer and merged into the TanStack Query cache — components never see raw WS/SSE payloads
7. Charts (uPlot/visx) re-render off the same cache keys used for the initial RSC paint — there is no separate "live" component tree
8. Mutations (budget edits, SLO threshold changes, template edits) go through tRPC mutations with Zod validation, optimistic update, and rollback on failure
9. Errors, slow queries, and dropped WS connections report to Sentry carrying the same `trace_id` the backend span carries, so a frontend error and its backend span can be correlated
