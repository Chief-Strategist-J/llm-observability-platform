# Next.js Extreme-Scale Architecture — Final Merged Reference

*Merges `nextjs-extreme-scale-patterns.md` + `nextjs-tracing-and-complex-logic.md` into one deduplicated, implementation-ready document. v2 adds the two things both source docs assumed but never showed — the actual data-driven core (schema/adapter/saga/slice) — plus a new generic transform layer for lists and JSON mapping. Nothing from v1 was removed, only renumbered and extended.*

## Table of Contents

1. [What the Merge Actually Fixes](#1-what-the-merge-actually-fixes)
2. [Build Order — Minimum Effort, Maximum Impact](#2-build-order--minimum-effort-maximum-impact)
3. [Final Unified Folder Structure](#3-final-unified-folder-structure)
4. [Complete Data-Driven Core](#4-complete-data-driven-core)
5. [Transform Layer — List & JSON Map, As Data](#5-transform-layer--list--json-map-as-data)
6. [Core Engine — Resilience, Rules, State, Events, Flags, Tracing, Workflows](#6-core-engine--resilience-rules-state-events-flags-tracing-workflows)
7. [Wiring One Feature End-to-End](#7-wiring-one-feature-end-to-end)
8. [Trace Waterfall — What One Click Produces](#8-trace-waterfall--what-one-click-produces)
9. [Complete Design Pattern Catalog](#9-complete-design-pattern-catalog)
10. [Domain Mapping Cheat Sheet](#10-domain-mapping-cheat-sheet)
11. [Scope Boundaries — What This Does Not Solve](#11-scope-boundaries--what-this-does-not-solve)
12. [Durable Execution — Making the Workflow Engine Actually Durable](#12-durable-execution--making-the-workflow-engine-actually-durable)
13. [Governance, RBAC & Audit Logging](#13-governance-rbac--audit-logging)
14. [Security Hardening Checklist](#14-security-hardening-checklist)
15. [Python Backend — Complete Mirror Architecture](#15-python-backend--complete-mirror-architecture)
16. [Compliance Primitives — Encryption, Erasure, Consent, Residency](#16-compliance-primitives--encryption-erasure-consent-residency)
17. [Production Readiness](#17-production-readiness)
18. [References](#18-references)

---

## 1. What the Merge Actually Fixes

Doc 2 says its additions are "extensions" of doc 1, but two of them are actually **replacements**, and one downstream file was never updated to match. If you'd pasted both docs into one repo as-is, this is where it would break:

| File | Doc 1 version | Doc 2 version | Resolution |
|---|---|---|---|
| `rules-engine/rule.types.ts` | Sync, no priority/category | Adds `priority`, `category`, `asyncCheck` | Doc 2 version wins — **superset**, not addition |
| `rules-engine/evaluate.ts` | `resolveEffects(rules, ctx): Set<string>` — **sync** | `resolveRules(rules, ctx): Promise<Rule[]>` — **async**, priority + deny-override, traced | Doc 2 version wins. This is a signature change, not an addition. |
| `state-machines/use-data-machine.ts` | Plain `useMachine` passthrough | Adds traced transitions via `actorRef.subscribe` | Doc 2 version wins — strict superset |
| `data-driven/adapter-decorators.ts` | `withRetry`, `withCache`, `withCircuitBreaker` | Adds `withTracing` | **Merged** — final file below exports all four |
| `feature-flags/resolve-flag.ts` | Calls `resolveEffects(...).has("enabled")` | **Never touched by doc 2** | **Broken as-is.** `resolveEffects` no longer exists once you adopt doc 2's `evaluate.ts`. Fixed below — flag resolution now calls `resolveRules` and is `async`. |

Everything else (event bus, field renderers, CQRS-lite selectors, folder structure) is additive with no conflicts.

---

## 2. Build Order — Minimum Effort, Maximum Impact

This is the direct answer to "minimum effort, highest impact." Don't build all of this at once — most of the payoff comes from six small files.

| Tier | Component | Effort | Impact | Why this tier |
|---|---|---|---|---|
| **1** | JSON Map (schema-driven `fromApi`/`toApi`) | Low — ~35 LOC | Very High | This *is* the anti-corruption layer. Without it, backend field-naming/shape drift leaks into every component that touches an entity. |
| **1** | List Transform (filter/search/sort/paginate) | Low — ~35 LOC | High | Every table/list view needs at least two of these; one generic function replaces N hand-rolled `.filter().sort().slice()` chains. |
| **1** | Decorator composition (`withRetry` / `withCache` / `withCircuitBreaker`) | Low — one file, ~40 LOC | High | Every adapter becomes resilient with one line at the call site. No per-feature code. |
| **1** | Event Bus | Low — ~15 LOC | High | Kills cross-feature import coupling immediately, zero dependencies. |
| **1** | Tracing setup + `withTracing` | Low–Med — mostly config | Very High | The single highest ROI item. One decorator + one SDK init call turns every adapter call into a searchable trace. |
| **1** | Rules Engine (flat list, sync is fine to start) | Low — ~60 LOC | High | Replaces the `if/else` forest immediately, even before you need priority or async conditions. |
| **2** | Feature Flags | Very low — reuses the rules engine | Med–High | Almost free once Tier 1's rules engine exists; ship-to-%-of-users becomes a config row. |
| **2** | CQRS-lite read models (`createSelector`) | Low | Med–High | Prevents recomputation on read-heavy dashboards; you already have Redux Toolkit, so this is memoization, not new infra. |
| **2** | Field Renderer Visitor Registry | Med | Med | Only pays off once you have 5+ field kinds. Below that, a switch statement is fine — don't build this early. |
| **3** | Rules Engine deepened (priority, deny-override, async checkers, `composeRuleSets`) | Med | High | Build this **when** rules start conflicting or need live data — not before. |
| **3** | State Machines (XState) | Med–High — new dependency, real learning curve | High, but only for multi-step flows | Worth it for flows with 4+ states or ambiguous transitions. Not worth it for a two-state toggle. |
| **4** | Workflow Engine (steps-as-data, DAG, traced runner) | High | Very high, but only if you're actually building an automation/workflow-builder feature | Don't build this speculatively. |
| **Infra** | Durable execution (Temporal), edge/ISR/PPR, micro-frontends | High / org-level | Situational | Not a frontend code decision — separate track, see §11. |

**If you build nothing else:** the six Tier 1 items above are comfortably under 300 total lines and convert an ad hoc, if/else, contract-fragile, unobservable adapter layer into one that's resilient, traced, contract-safe, and rule-driven. That's the 20% of this document that gets you 80% of the value — everything past Tier 2 should be pulled in only when a real requirement forces it, not speculatively.

---

## 3. Final Unified Folder Structure

```
my-app/
├── apps/
│   └── web/
│       ├── app/
│       │   ├── (public)/login/page.tsx
│       │   ├── (protected)/<feature>/page.tsx        # e.g. wallet, dashboard, work-order
│       │   ├── layout.tsx
│       │   ├── providers.tsx                          # mounts store, event-bus listeners, flag context
│       │   └── middleware.ts
│       ├── e2e/
│       ├── playwright.config.ts
│       └── next.config.ts
│
├── packages/
│   ├── core/
│   │   ├── store/
│   │   │   ├── feature-registry.ts                    # every feature's reducer+saga, central
│   │   │   ├── configure-store.ts
│   │   │   └── root-saga.ts
│   │   ├── http/
│   │   │   └── http-client.ts                         # thin fetch facade, auto-traced by FetchInstrumentation
│   │   ├── tracing/
│   │   │   └── tracer.ts                               # OTEL Web SDK + OTLP + fetch auto-instrumentation
│   │   ├── data-driven/
│   │   │   ├── entity-schema.types.ts                  # the contract everything else reads
│   │   │   ├── transform.types.ts                      # ListOp / JsonMapOp — transforms AS DATA
│   │   │   ├── list-transform.ts                       # filter/search/sort/paginate/pick/groupBy
│   │   │   ├── json-map.ts                             # rename/pick/omit/default/coerce — the anti-corruption layer
│   │   │   ├── create-entity-adapter.ts                # generic CRUD adapter factory
│   │   │   ├── create-entity-sagas.ts                  # generic saga factory
│   │   │   ├── create-entity-slice.ts                  # generic slice factory
│   │   │   ├── adapter-decorators.ts                   # withRetry / withCache / withCircuitBreaker / withTracing
│   │   │   └── register-entity.ts                      # wires adapter+saga+slice+registry in one call
│   │   ├── rules-engine/
│   │   │   ├── rule.types.ts                           # Rule, RuleCondition, priority, category, asyncCheck
│   │   │   ├── async-checkers.ts                       # registry for live-data-dependent conditions
│   │   │   ├── evaluate.ts                             # resolveRules — async, priority + deny-override, traced
│   │   │   └── compose-rules.ts                        # merge global + tenant + feature rule sets
│   │   ├── state-machines/
│   │   │   └── use-data-machine.ts                     # generic XState hook, traced transitions
│   │   ├── workflow-engine/
│   │   │   ├── step.types.ts
│   │   │   ├── step-registry.ts                        # Visitor pattern — no central switch
│   │   │   ├── builtin-steps.ts                        # evaluateRules / callEntity / callAI / branch / parallel / humanApproval
│   │   │   └── run-workflow.ts                         # traced root span + per-step child spans
│   │   ├── feature-flags/
│   │   │   └── resolve-flag.ts                         # flags = rules + rollout %, now async (see §1)
│   │   ├── event-bus/
│   │   │   └── event-bus.ts                            # cross-feature pub/sub
│   │   └── testing/
│   │       ├── test-store.ts
│   │       └── msw-handlers/                           # shared by tests AND Storybook
│   │
│   ├── shared/
│   │   ├── ui/
│   │   │   ├── DataForm.tsx                            # schema-driven form, zero per-entity markup
│   │   │   ├── DataTable.tsx                           # schema-driven table, uses list-transform for search/sort/page
│   │   │   └── field-renderers/
│   │   │       ├── registry.ts                         # Visitor registry — no central switch
│   │   │       └── builtins.ts                         # text/number/select/date/boolean registered once
│   │   ├── lib/
│   │   │   └── current-trace-id.ts                     # surfaces trace ID to error toasts / support
│   │   └── types/
│   │
│   ├── features/
│   │   ├── <feature>/                                  # template: wallet, work-order, deal, automation-definition, agent-run...
│   │   │   ├── schema/<feature>.schema.ts              # CRUD shape + fromApi/toApi transform ops
│   │   │   ├── rules/<feature>.rules.ts                # business branches, AS DATA (priority/category/async as needed)
│   │   │   ├── machines/<feature>.machine.ts           # multi-step flow, AS DATA
│   │   │   ├── workflows/<feature>-automation.workflow.ts
│   │   │   ├── overrides/                              # hand-written — ONLY non-generic logic lives here
│   │   │   ├── readModels/
│   │   │   │   └── <feature>-summary.selector.ts       # CQRS-lite: memoized derived reads
│   │   │   ├── ui/
│   │   │   │   ├── <Feature>Form.stories.tsx
│   │   │   │   └── <Feature>Flow.tsx                   # consumes the machine via useDataMachine
│   │   │   ├── tests/<feature>.rules.test.ts
│   │   │   └── index.ts                                # registerEntity + rule/machine registration
│   │   ├── notifications/                              # subscribes via event-bus — imports nothing from other features
│   │   ├── dashboard/
│   │   └── auth/
│   │
│   └── config/
│       ├── eslint-boundaries.config.js
│       └── env.schema.ts
│
├── .github/workflows/{ci.yml, deploy.yml}
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

Everything under `core/` is written once and shared. Everything under `features/<feature>/` is the only place per-feature code lives — and most of those files are data (schema, rules, machine config), not logic.

---

## 4. Complete Data-Driven Core

Both source docs said "extends `nextjs-frontend-architecture.md` and `nextjs-data-driven-layer.md` — those still hold for the base CRUD-generation code" and built on top of `create-entity-adapter.ts`, `create-entity-sagas.ts`, `create-entity-slice.ts` without ever showing them. Here's that base layer, so this document is self-contained end to end.

### 4.1 Entity Schema — the contract everything else reads

```typescript
// packages/core/data-driven/entity-schema.types.ts
import type { z } from "zod";
import type { JsonMapOp } from "./transform.types";

export type FieldKind = "text" | "number" | "select" | "date" | "boolean";

export interface FieldConfig<T = unknown> {
  key: string;
  label: string;
  kind: FieldKind;
  required?: boolean;
  options?: { label: string; value: T }[];   // for "select"
  defaultValue?: T;
}

export interface EntitySchema<T = Record<string, unknown>> {
  name: string;               // "wallet" — used as trace name, event prefix, store slice key
  endpoint: string;           // "/api/wallets"
  fields: FieldConfig[];
  validate: z.ZodType<T>;     // zod schema — the runtime half of the anti-corruption boundary
  fromApi?: JsonMapOp[];      // raw API JSON -> internal entity shape (§5.2)
  toApi?: JsonMapOp[];        // internal entity shape -> API JSON on write (§5.2)
}
```

### 4.2 HTTP Client — thin fetch facade

Deliberately minimal: retry, caching, and circuit-breaking live one layer up in `adapter-decorators.ts` (§6.2), not here. Using `fetch` means `FetchInstrumentation` (§6.1) auto-traces every call for free.

```typescript
// packages/core/http/http-client.ts
async function request(method: string, url: string, body?: unknown) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${url} failed: ${res.status}`);
  return { data: await res.json() };
}

export const httpClient = {
  get: (url: string) => request("GET", url),
  post: (url: string, body: unknown) => request("POST", url, body),
  patch: (url: string, body: unknown) => request("PATCH", url, body),
  delete: (url: string) => request("DELETE", url),
};
```

### 4.3 Feature Registry + Store Wiring

```typescript
// packages/core/store/feature-registry.ts
interface FeatureModule { reducer: any; saga: () => Generator }
const registry = new Map<string, FeatureModule>();
export const featureRegistry = {
  register(name: string, mod: FeatureModule) { registry.set(name, mod); },
  getAll() { return [...registry.entries()]; },
};
```

```typescript
// packages/core/store/root-saga.ts
import { all } from "redux-saga/effects";
import { featureRegistry } from "./feature-registry";

export function* rootSaga() {
  yield all(featureRegistry.getAll().map(([, mod]) => mod.saga()));
}
```

```typescript
// packages/core/store/configure-store.ts
import { configureStore } from "@reduxjs/toolkit";
import createSagaMiddleware from "redux-saga";
import { featureRegistry } from "./feature-registry";
import { rootSaga } from "./root-saga";

const sagaMiddleware = createSagaMiddleware();
export const store = configureStore({
  reducer: Object.fromEntries(featureRegistry.getAll().map(([name, mod]) => [name, mod.reducer])),
  middleware: (getDefault) => getDefault().concat(sagaMiddleware),
});
sagaMiddleware.run(rootSaga);
```

**Ordering gotcha worth knowing:** every feature's `index.ts` must run (and call `registerEntity`) *before* `configure-store.ts` reads the registry. In practice this means a single barrel import of all features in `providers.tsx`, imported before the store is created.

### 4.4 Entity Adapter Factory — generic CRUD, JSON mapping applied automatically

```typescript
// packages/core/data-driven/create-entity-adapter.ts
import { httpClient } from "@core/http/http-client";
import { mapJson } from "./json-map";
import type { EntitySchema } from "./entity-schema.types";

export interface CrudPort<T> {
  list(): Promise<T[]>;
  get(id: string): Promise<T>;
  create(payload: Partial<T>): Promise<T>;
  update(id: string, payload: Partial<T>): Promise<T>;
  remove(id: string): Promise<void>;
}

export function createEntityAdapter<T extends Record<string, unknown>>(schema: EntitySchema<T>): CrudPort<T> {
  const fromApi = (raw: unknown): T =>
    schema.validate.parse(schema.fromApi ? mapJson(raw as Record<string, unknown>, schema.fromApi) : raw);
  const toApi = (entity: Partial<T>) =>
    schema.toApi ? mapJson(entity as Record<string, unknown>, schema.toApi) : entity;

  return {
    async list() {
      const { data } = await httpClient.get(schema.endpoint);
      return (data as unknown[]).map(fromApi);
    },
    async get(id) {
      const { data } = await httpClient.get(`${schema.endpoint}/${id}`);
      return fromApi(data);
    },
    async create(payload) {
      const { data } = await httpClient.post(schema.endpoint, toApi(payload));
      return fromApi(data);
    },
    async update(id, payload) {
      const { data } = await httpClient.patch(`${schema.endpoint}/${id}`, toApi(payload));
      return fromApi(data);
    },
    async remove(id) {
      await httpClient.delete(`${schema.endpoint}/${id}`);
    },
  };
}
```

One factory, driven entirely by `schema.fromApi`/`schema.toApi` (§5.2) — no hand-written mapping code per entity, ever.

### 4.5 Entity Slice Factory (Redux Toolkit)

```typescript
// packages/core/data-driven/create-entity-slice.ts
import { createEntityAdapter as createRtkAdapter, createSlice, type PayloadAction } from "@reduxjs/toolkit";

export function createEntitySlice<T extends { id: string }>(name: string) {
  const rtkAdapter = createRtkAdapter<T>();
  const slice = createSlice({
    name,
    initialState: rtkAdapter.getInitialState({ status: "idle" as "idle" | "loading" | "error" }),
    reducers: {
      setAll: rtkAdapter.setAll,
      upsertOne: rtkAdapter.upsertOne,
      removeOne: rtkAdapter.removeOne,
      setStatus(state, action: PayloadAction<"idle" | "loading" | "error">) {
        state.status = action.payload;
      },
    },
  });
  return { slice, selectors: rtkAdapter.getSelectors() };
}
```

### 4.6 Entity Saga Factory

```typescript
// packages/core/data-driven/create-entity-sagas.ts
import { call, put, takeEvery } from "redux-saga/effects";
import { eventBus } from "@core/event-bus/event-bus";
import type { CrudPort } from "./create-entity-adapter";

export function createEntitySagas<T extends { id: string }>(name: string, adapter: CrudPort<T>, slice: any) {
  function* fetchAll() {
    yield put(slice.actions.setStatus("loading"));
    try {
      const items: T[] = yield call(adapter.list);
      yield put(slice.actions.setAll(items));
      yield put(slice.actions.setStatus("idle"));
    } catch {
      yield put(slice.actions.setStatus("error"));
    }
  }
  function* createOne(action: { payload: Partial<T> }) {
    const item: T = yield call(adapter.create, action.payload);
    yield put(slice.actions.upsertOne(item));
    eventBus.emit(`${name}.created`, item);   // generic cross-feature hook — see §6.5
  }
  function* removeOne(action: { payload: string }) {
    yield call(adapter.remove, action.payload);
    yield put(slice.actions.removeOne(action.payload));
    eventBus.emit(`${name}.removed`, { id: action.payload });
  }
  return function* rootSaga() {
    yield takeEvery(`${name}/fetchAll`, fetchAll);
    yield takeEvery(`${name}/createOne`, createOne);
    yield takeEvery(`${name}/removeOne`, removeOne);
  };
}
```

### 4.7 register-entity — wires it all together

```typescript
// packages/core/data-driven/register-entity.ts
import { featureRegistry } from "@core/store/feature-registry";
import { createEntitySlice } from "./create-entity-slice";
import { createEntitySagas } from "./create-entity-sagas";
import type { CrudPort } from "./create-entity-adapter";
import type { EntitySchema } from "./entity-schema.types";

export function registerEntity<T extends { id: string }>(schema: EntitySchema<T>, adapter: CrudPort<T>) {
  const { slice, selectors } = createEntitySlice<T>(schema.name);
  const saga = createEntitySagas<T>(schema.name, adapter, slice);
  featureRegistry.register(schema.name, { reducer: slice.reducer, saga });
  return { schema, adapter, slice, selectors, actions: slice.actions };
}
```

### 4.8 DataForm & DataTable — generic UI driven by schema

```tsx
// packages/shared/ui/DataForm.tsx
import { useState } from "react";
import { FieldRenderer } from "./field-renderers/registry";
import type { EntitySchema } from "@core/data-driven/entity-schema.types";

export function DataForm<T extends Record<string, unknown>>({
  schema, initial, onSubmit,
}: { schema: EntitySchema<T>; initial?: Partial<T>; onSubmit: (values: Partial<T>) => void }) {
  const [values, setValues] = useState<Partial<T>>(initial ?? {});
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(values); }}>
      {schema.fields.map((field) => (
        <FieldRenderer
          key={field.key}
          field={field}
          value={values[field.key as keyof T]}
          onChange={(v) => setValues((prev) => ({ ...prev, [field.key]: v }))}
        />
      ))}
      <button type="submit">Save</button>
    </form>
  );
}
```

```tsx
// packages/shared/ui/DataTable.tsx
import { useMemo, useState } from "react";
import { transformList } from "@core/data-driven/list-transform";
import type { EntitySchema } from "@core/data-driven/entity-schema.types";
import type { ListOp } from "@core/data-driven/transform.types";

export function DataTable<T extends Record<string, unknown>>({
  schema, rows, extraOps = [],
}: { schema: EntitySchema<T>; rows: T[]; extraOps?: ListOp[] }) {
  const [query, setQuery] = useState("");
  const visible = useMemo(() => {
    const ops: ListOp[] = query
      ? [{ op: "search", fields: schema.fields.map((f) => f.key), query }, ...extraOps]
      : extraOps;
    return transformList(rows, ops);
  }, [rows, query, extraOps, schema.fields]);

  return (
    <div>
      <input placeholder="Search..." value={query} onChange={(e) => setQuery(e.target.value)} />
      <table>
        <thead><tr>{schema.fields.map((f) => <th key={f.key}>{f.label}</th>)}</tr></thead>
        <tbody>
          {visible.map((row: any) => (
            <tr key={row.id}>{schema.fields.map((f) => <td key={f.key}>{String(row[f.key] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

`DataTable` never gets per-feature search/sort/pagination code — it delegates to `transformList` (§5.1), which is exactly the "minimum code, high impact" ask: one generic function, reused by every table in the app.

---

## 5. Transform Layer — List & JSON Map, As Data

Same idea as the rules engine (§6.3) and workflow engine (§6.9): instead of writing `.filter().sort().slice()` by hand in every component, or a bespoke mapper per entity, **shaping operations are data** — an array of `{ op, ... }` objects evaluated by one small generic function.

### 5.1 List Transform Ops — full reference

```typescript
// packages/core/data-driven/transform.types.ts (list half)
export type ListOp =
  | { op: "filter"; field: string; match: "eq" | "neq" | "in" | "gt" | "lt" | "gte" | "lte" | "contains"; value: unknown }
  | { op: "search"; fields: string[]; query: string }
  | { op: "sort"; field: string; dir?: "asc" | "desc" }
  | { op: "paginate"; page: number; pageSize: number }
  | { op: "pick"; fields: string[] };
```

```typescript
// packages/core/data-driven/list-transform.ts
import get from "lodash/get";
import type { ListOp } from "./transform.types";

function matches(value: unknown, match: string, target: unknown): boolean {
  switch (match) {
    case "eq":  return value === target;
    case "neq": return value !== target;
    case "in":  return Array.isArray(target) && target.includes(value);
    case "gt":  return Number(value) > Number(target);
    case "lt":  return Number(value) < Number(target);
    case "gte": return Number(value) >= Number(target);
    case "lte": return Number(value) <= Number(target);
    case "contains": return String(value ?? "").toLowerCase().includes(String(target).toLowerCase());
    default: return false;
  }
}

export function transformList<T extends Record<string, unknown>>(list: T[], ops: ListOp[]): T[] {
  return ops.reduce((result, op) => {
    switch (op.op) {
      case "filter":
        return result.filter((item) => matches(get(item, op.field), op.match, op.value));
      case "search": {
        const q = op.query.toLowerCase();
        return result.filter((item) => op.fields.some((f) => String(get(item, f) ?? "").toLowerCase().includes(q)));
      }
      case "sort": {
        const dir = op.dir === "desc" ? -1 : 1;
        return [...result].sort((a, b) => (get(a, op.field) > get(b, op.field) ? dir : -dir));
      }
      case "paginate": {
        const start = (op.page - 1) * op.pageSize;
        return result.slice(start, start + op.pageSize);
      }
      case "pick":
        return result.map((item) => op.fields.reduce((acc, f) => ({ ...acc, [f]: get(item, f) }), {} as T));
      default:
        return result;
    }
  }, list);
}

// groupBy changes shape (array -> map), so it's a terminal operation, not part of the reduce chain above
export function groupByList<T extends Record<string, unknown>>(list: T[], field: string): Record<string, T[]> {
  return list.reduce((acc, item) => {
    const key = String(get(item, field));
    (acc[key] ??= []).push(item);
    return acc;
  }, {} as Record<string, T[]>);
}
```

| Op | Signature | Underlying method(s) | What it does | Example |
|---|---|---|---|---|
| `filter` | `{ op: "filter", field, match, value }` | `Array.prototype.filter` + `lodash.get` | Keep items where `field` satisfies `match` against `value` | `{ op: "filter", field: "status", match: "eq", value: "active" }` |
| `search` | `{ op: "search", fields, query }` | `Array.prototype.filter` + `String.prototype.includes` | Case-insensitive substring match across multiple fields | `{ op: "search", fields: ["name","email"], query: "acme" }` |
| `sort` | `{ op: "sort", field, dir? }` | `Array.prototype.sort` | Sort ascending (default) or descending by field | `{ op: "sort", field: "createdAt", dir: "desc" }` |
| `paginate` | `{ op: "paginate", page, pageSize }` | `Array.prototype.slice` | Slice to one page, 1-indexed | `{ op: "paginate", page: 2, pageSize: 20 }` |
| `pick` | `{ op: "pick", fields }` | `Array.prototype.map` + `lodash.get` | Project each item down to a subset of fields | `{ op: "pick", fields: ["id","name"] }` |
| `groupBy` *(terminal, separate fn)* | `groupByList(list, field)` | `Array.prototype.reduce` + `lodash.get` | Bucket items into `Record<string, T[]>` by field value | `groupByList(wallets, "currency")` |

`match` operators for `filter`: `eq`, `neq`, `in`, `gt`, `lt`, `gte`, `lte`, `contains`.

Chained usage — this replaces every hand-rolled `.filter().sort().slice()` in the app:

```typescript
const page = transformList(wallets, [
  { op: "filter", field: "status", match: "eq", value: "active" },
  { op: "sort", field: "balance", dir: "desc" },
  { op: "paginate", page: 1, pageSize: 25 },
]);
```

### 5.2 JSON Map Ops — full reference (the anti-corruption layer, made concrete)

```typescript
// packages/core/data-driven/transform.types.ts (JSON half)
export type JsonMapOp =
  | { op: "rename"; from: string; to: string }
  | { op: "pick"; fields: string[] }
  | { op: "omit"; fields: string[] }
  | { op: "default"; field: string; value: unknown }
  | { op: "coerce"; field: string; to: "string" | "number" | "boolean" | "date" };
```

```typescript
// packages/core/data-driven/json-map.ts
import get from "lodash/get";
import set from "lodash/set";
import type { JsonMapOp } from "./transform.types";

const coercers: Record<string, (v: unknown) => unknown> = {
  string:  (v) => String(v),
  number:  (v) => Number(v),
  boolean: (v) => Boolean(v),
  date:    (v) => new Date(v as string),
};

export function mapJson(input: Record<string, unknown>, ops: JsonMapOp[]): Record<string, unknown> {
  return ops.reduce((out, op) => {
    switch (op.op) {
      case "rename": {
        const value = get(out, op.from);
        const next = { ...out };
        set(next, op.to, value);
        if (op.from !== op.to) delete next[op.from];
        return next;
      }
      case "pick":
        return op.fields.reduce((acc, f) => set(acc, f, get(out, f)), {} as Record<string, unknown>);
      case "omit": {
        const next = { ...out };
        op.fields.forEach((f) => delete next[f]);
        return next;
      }
      case "default": {
        if (get(out, op.field) != null) return out;
        const next = { ...out };
        set(next, op.field, op.value);
        return next;
      }
      case "coerce": {
        const value = get(out, op.field);
        if (value == null) return out;
        const next = { ...out };
        set(next, op.field, coercers[op.to](value));
        return next;
      }
      default:
        return out;
    }
  }, { ...input });
}

export function mapJsonList(list: Record<string, unknown>[], ops: JsonMapOp[]): Record<string, unknown>[] {
  return list.map((item) => mapJson(item, ops));
}
```

| Op | Signature | Underlying method(s) | What it does | Example |
|---|---|---|---|---|
| `rename` | `{ op: "rename", from, to }` | `lodash.get`/`set` + `delete` | Move/rename a field, dot-path aware | `{ op: "rename", from: "owner_name", to: "ownerName" }` |
| `pick` | `{ op: "pick", fields }` | `Array.prototype.reduce` + `lodash.get`/`set` | Keep only listed fields | `{ op: "pick", fields: ["id","balance"] }` |
| `omit` | `{ op: "omit", fields }` | object spread + `delete` | Drop listed fields | `{ op: "omit", fields: ["internal_flag"] }` |
| `default` | `{ op: "default", field, value }` | `lodash.get`/`set` with nullish check | Fill in a value only if missing/null | `{ op: "default", field: "currency", value: "USD" }` |
| `coerce` | `{ op: "coerce", field, to }` | `String()` / `Number()` / `Boolean()` / `new Date()` | Type-cast a field | `{ op: "coerce", field: "balance", to: "number" }` |

### 5.3 Schema-Driven Mapping, End to End

This is what `EntitySchema.fromApi`/`toApi` (§4.1) actually looks like for a real entity — backend snake_case, frontend camelCase, zero hand-written mapping code:

```typescript
// packages/features/wallet/schema/wallet.schema.ts
import { z } from "zod";
import type { EntitySchema } from "@core/data-driven/entity-schema.types";

const walletZod = z.object({
  id: z.string(),
  ownerName: z.string(),
  balance: z.number(),
  currency: z.string(),
});
type Wallet = z.infer<typeof walletZod>;

export const walletSchema: EntitySchema<Wallet> = {
  name: "wallet",
  endpoint: "/api/wallets",
  fields: [
    { key: "ownerName", label: "Owner", kind: "text", required: true },
    { key: "balance", label: "Balance", kind: "number" },
    { key: "currency", label: "Currency", kind: "select", options: [{ label: "USD", value: "USD" }, { label: "EUR", value: "EUR" }] },
  ],
  validate: walletZod,
  fromApi: [
    { op: "rename", from: "owner_name", to: "ownerName" },   // backend snake_case -> frontend camelCase
    { op: "coerce", field: "balance", to: "number" },         // backend sometimes sends balance as a string
    { op: "default", field: "currency", value: "USD" },       // legacy rows predate the currency column
  ],
  toApi: [
    { op: "rename", from: "ownerName", to: "owner_name" },    // mirror on write
  ],
};
```

Every future entity gets the same treatment: declare the field renames/coercions/defaults as data in its schema, and `createEntityAdapter` (§4.4) applies them automatically on every `list`/`get`/`create`/`update` call. No entity ever needs its own hand-written `toWallet()`/`fromWallet()` function.

---

## 6. Core Engine — Resilience, Rules, State, Events, Flags, Tracing, Workflows

### 6.1 Tracing setup

```typescript
// packages/core/tracing/tracer.ts
import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { ZoneContextManager } from "@opentelemetry/context-zone";     // browsers need this — no native AsyncLocalStorage
import { W3CTraceContextPropagator } from "@opentelemetry/core";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { trace } from "@opentelemetry/api";

const provider = new WebTracerProvider({
  resource: resourceFromAttributes({ [ATTR_SERVICE_NAME]: "frontend" }),
});
provider.addSpanProcessor(
  new BatchSpanProcessor(new OTLPTraceExporter({ url: process.env.NEXT_PUBLIC_OTLP_ENDPOINT })) // must end in /v1/traces
);
provider.register({
  contextManager: new ZoneContextManager(),
  propagator: new W3CTraceContextPropagator(),
});

// auto-injects traceparent into every fetch() — this is what links a frontend span to
// whatever backend span your API creates from the same header, same OTLP pipeline
registerInstrumentations({
  instrumentations: [
    new FetchInstrumentation({
      propagateTraceHeaderCorsUrls: [new RegExp(process.env.NEXT_PUBLIC_API_ORIGIN!)],
      // ^ restrict to your real API origin(s) — a wildcard here leaks trace headers to third-party requests
    }),
  ],
});

export const tracer = trace.getTracer("frontend");
```

OTLP lands in whatever backend you already run — Tempo, Jaeger, Honeycomb — alongside backend spans, in the same trace. The OTEL JS surface moves fast; check current package versions before wiring this in for real (see §12).

### 6.2 Adapter decorators — final merged file

The single file where doc 1's three decorators and doc 2's fourth combine. **Composition order matters**: tracing goes outermost so its span covers retry backoff and cache-miss latency, not just the final attempt.

```typescript
// packages/core/data-driven/adapter-decorators.ts
import type { CrudPort } from "./create-entity-adapter";
import { tracer } from "@core/tracing/tracer";

export function withRetry<T>(adapter: CrudPort<T>, attempts = 3): CrudPort<T> {
  const wrap = (fn: Function) => async (...args: any[]) => {
    for (let i = 0; i < attempts; i++) {
      try { return await fn(...args); } catch (e) { if (i === attempts - 1) throw e; }
    }
  };
  return { list: wrap(adapter.list), get: wrap(adapter.get), create: wrap(adapter.create), update: wrap(adapter.update), remove: wrap(adapter.remove) } as CrudPort<T>;
}

export function withCache<T>(adapter: CrudPort<T>, ttlMs = 30_000): CrudPort<T> {
  let cache: { at: number; data: T[] } | null = null;
  return {
    ...adapter,
    async list() {
      if (cache && Date.now() - cache.at < ttlMs) return cache.data;
      const data = await adapter.list();
      cache = { at: Date.now(), data };
      return data;
    },
  };
}

export function withCircuitBreaker<T>(adapter: CrudPort<T>, failureThreshold = 5, resetMs = 15_000): CrudPort<T> {
  let failures = 0, openedAt = 0;
  const guard = (fn: Function) => async (...args: any[]) => {
    if (failures >= failureThreshold && Date.now() - openedAt < resetMs) throw new Error("circuit open");
    try { const r = await fn(...args); failures = 0; return r; }
    catch (e) { failures++; if (failures === failureThreshold) openedAt = Date.now(); throw e; }
  };
  return { list: guard(adapter.list), get: guard(adapter.get), create: guard(adapter.create), update: guard(adapter.update), remove: guard(adapter.remove) } as CrudPort<T>;
}

export function withTracing<T>(adapter: CrudPort<T>, entityName: string): CrudPort<T> {
  const wrap = (fn: Function, op: string) => (...args: any[]) =>
    tracer.startActiveSpan(`${entityName}.${op}`, async (span) => {
      span.setAttribute("entity.name", entityName);
      span.setAttribute("entity.op", op);
      try {
        const result = await fn(...args);
        span.setStatus({ code: 1 });
        return result;
      } catch (e) {
        span.recordException(e as Error);
        span.setStatus({ code: 2, message: String(e) });
        throw e;
      } finally {
        span.end();
      }
    });
  return {
    list: wrap(adapter.list, "list"), get: wrap(adapter.get, "get"),
    create: wrap(adapter.create, "create"), update: wrap(adapter.update, "update"),
    remove: wrap(adapter.remove, "remove"),
  } as CrudPort<T>;
}
```

Applied once per entity, declaratively — tracing outermost:

```typescript
const adapter = withTracing(withCircuitBreaker(withCache(withRetry(raw))), "wallet");
```

### 6.3 Rules Engine — final version (doc 2's async version supersedes doc 1's)

```typescript
// packages/core/rules-engine/rule.types.ts
export interface RuleContext {
  user: { id: string; tier: "free" | "pro" | "enterprise"; region: string; kycStatus?: "verified" | "pending" | "none" };
  entity?: Record<string, unknown>;
  now: Date;
}

export type RuleCondition =
  | { op: "eq"; field: string; value: unknown }
  | { op: "in"; field: string; values: unknown[] }
  | { op: "gt" | "lt" | "gte" | "lte"; field: string; value: number }
  | { op: "and"; conditions: RuleCondition[] }
  | { op: "or"; conditions: RuleCondition[] }
  | { op: "not"; condition: RuleCondition }
  | { op: "asyncCheck"; resolver: string };   // live-data-dependent conditions — see 6.3.1

export interface Rule {
  id: string;
  description: string;
  when: RuleCondition;
  effect: string;                            // "deny.withdraw", "fee.withdraw:0", "flow.withdraw:extra-confirmation", ...
  priority?: number;                         // higher wins among matched non-deny rules
  category?: "allow" | "deny" | "modify";    // "deny" always wins, regardless of priority — safety default
}
```

**6.3.1 Async checkers** — same registry shape as field renderers (§4.8's sibling, `field-renderers/registry.ts`) and workflow steps (§6.9), reused a third time:

```typescript
// packages/core/rules-engine/async-checkers.ts
type AsyncChecker = (ctx: RuleContext) => Promise<boolean>;
const checkers = new Map<string, AsyncChecker>();
export function registerAsyncChecker(key: string, fn: AsyncChecker) { checkers.set(key, fn); }
export function getAsyncChecker(key: string): AsyncChecker {
  const fn = checkers.get(key);
  if (!fn) throw new Error(`No async checker registered for "${key}"`);
  return fn;
}
```

**6.3.2 Evaluator** — async-aware, traced, priority + deny-override resolution. This is the only `evaluate.ts` — doc 1's sync `resolveEffects` is fully replaced:

```typescript
// packages/core/rules-engine/evaluate.ts
import get from "lodash/get";
import { tracer } from "@core/tracing/tracer";
import { getAsyncChecker } from "./async-checkers";
import type { Rule, RuleCondition, RuleContext } from "./rule.types";

async function evalConditionAsync(cond: RuleCondition, ctx: RuleContext): Promise<boolean> {
  switch (cond.op) {
    case "eq":  return get(ctx, cond.field) === cond.value;
    case "in":  return cond.values.includes(get(ctx, cond.field));
    case "gt":  return Number(get(ctx, cond.field)) > cond.value;
    case "lt":  return Number(get(ctx, cond.field)) < cond.value;
    case "gte": return Number(get(ctx, cond.field)) >= cond.value;
    case "lte": return Number(get(ctx, cond.field)) <= cond.value;
    case "and": return (await Promise.all(cond.conditions.map((c) => evalConditionAsync(c, ctx)))).every(Boolean);
    case "or":  return (await Promise.all(cond.conditions.map((c) => evalConditionAsync(c, ctx)))).some(Boolean);
    case "not": return !(await evalConditionAsync(cond.condition, ctx));
    case "asyncCheck":
      return tracer.startActiveSpan(`rules.async.${cond.resolver}`, async (span) => {
        const result = await getAsyncChecker(cond.resolver)(ctx);
        span.setAttribute("result", result);
        span.end();
        return result;
      });
  }
}

export async function resolveRules(rules: Rule[], ctx: RuleContext): Promise<Rule[]> {
  return tracer.startActiveSpan("rules.evaluate", async (span) => {
    const checked = await Promise.all(rules.map(async (r) => ({ rule: r, matched: await evalConditionAsync(r.when, ctx) })));
    const matched = checked.filter((c) => c.matched).map((c) => c.rule);
    const denies = matched.filter((r) => r.category === "deny");
    const winners = denies.length ? denies : matched.sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

    span.setAttribute("rules.total", rules.length);
    span.setAttribute("rules.matched_ids", matched.map((r) => r.id).join(","));
    span.setAttribute("rules.winning_ids", winners.map((r) => r.id).join(","));
    span.end();
    return winners;
  });
}
```

**6.3.3 Composing layered rule sets:**

```typescript
// packages/core/rules-engine/compose-rules.ts
export function composeRuleSets(...ruleSets: Rule[][]): Rule[] {
  return ruleSets.flat();
}
// usage: resolveRules(composeRuleSets(globalComplianceRules, tenantRules, featureRules), ctx)
```

**6.3.4 A feature's rules — this is the "thousand branches" surface:**

```typescript
// packages/features/wallet/rules/wallet.rules.ts
import type { Rule } from "@core/rules-engine/rule.types";

export const walletRules: Rule[] = [
  { id: "w1", description: "Only KYC-verified users can withdraw",
    when: { op: "not", condition: { op: "eq", field: "user.kycStatus", value: "verified" } },
    category: "deny", effect: "deny.withdraw" },
  { id: "w2", description: "Enterprise tier gets zero withdrawal fee",
    when: { op: "eq", field: "user.tier", value: "enterprise" },
    priority: 10, effect: "fee.withdraw:0" },
  { id: "w3", description: "EU region requires an extra confirmation step",
    when: { op: "in", field: "user.region", values: ["DE", "FR", "IT", "ES"] },
    effect: "flow.withdraw:extra-confirmation" },
  // rule #4...#1000 are this exact shape. A new business condition is a new row, not a new deploy.
];
```

Usage — no branch forest in the component:

```tsx
const winners = await resolveRules(walletRules, ctx);
const effects = new Set(winners.map((r) => r.effect));
if (effects.has("deny.withdraw")) return <WithdrawDisabled />;
const fee = effects.has("fee.withdraw:0") ? 0 : defaultFee;
```

### 6.4 State Machines — traced

```typescript
// packages/features/wallet/machines/withdrawal.machine.ts
import { setup } from "xstate";

export const withdrawalMachine = setup({}).createMachine({
  id: "withdrawal",
  initial: "idle",
  states: {
    idle:       { on: { SUBMIT: "validating" } },
    validating: { on: { VALID: "confirming", INVALID: "idle" } },
    confirming: { on: { CONFIRM: "processing", CANCEL: "idle" } },   // rule w3 can route here
    processing: { on: { SUCCESS: "done", FAILURE: "failed" } },
    failed:     { on: { RETRY: "processing", ABANDON: "idle" } },
    done:       { type: "final" },
  },
});
```

```typescript
// packages/core/state-machines/use-data-machine.ts
import { useMachine } from "@xstate/react";
import { useEffect } from "react";
import { tracer } from "@core/tracing/tracer";
import type { StateMachine } from "xstate";

export function useDataMachine(machine: StateMachine<any, any, any>, traceName = machine.id) {
  const [state, send, actorRef] = useMachine(machine);
  useEffect(() => {
    const sub = actorRef.subscribe((snapshot) => {
      tracer.startSpan(`${traceName}.transition`, { attributes: { "machine.state": String(snapshot.value) } }).end();
    });
    return () => sub.unsubscribe();
  }, [actorRef, traceName]);
  return [state, send, actorRef] as const;
}
```

Every transition becomes a timestamped span — "why was this stuck in `processing` for 40 seconds" becomes a trace lookup instead of log spelunking.

### 6.5 Event Bus

```typescript
// packages/core/event-bus/event-bus.ts
type Handler<T> = (payload: T) => void;
class EventBus {
  private handlers = new Map<string, Set<Handler<any>>>();
  on<T>(event: string, handler: Handler<T>) {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)!.delete(handler);
  }
  emit<T>(event: string, payload: T) {
    this.handlers.get(event)?.forEach((h) => h(payload));
  }
}
export const eventBus = new EventBus();
```

The wallet saga emits `eventBus.emit("wallet.withdrawal.completed", payload)`; `notifications` calls `eventBus.on(...)` in its own saga setup. Neither imports the other, and `eslint-plugin-boundaries` still passes.

### 6.6 Feature Flags — fixed to match the new evaluator (see §1)

Doc 1's version called a function (`resolveEffects`) that no longer exists once you adopt doc 2's rules engine. This is the reconciled version:

```typescript
// packages/core/feature-flags/resolve-flag.ts
import { resolveRules } from "@core/rules-engine/evaluate";
import type { Rule, RuleContext } from "@core/rules-engine/rule.types";

interface FlagConfig { key: string; rules: Rule[]; rolloutPercent?: number }

export async function resolveFlag(flag: FlagConfig, ctx: RuleContext): Promise<boolean> {
  if (flag.rolloutPercent != null) return hashUserId(ctx.user.id) % 100 < flag.rolloutPercent;
  const winners = await resolveRules(flag.rules, ctx);
  return winners.some((r) => r.effect === "enabled");
}
```

A flag is a named rule with a rollout percentage — no separate system, and "ship to 5% of enterprise users in the EU" is a config change, not a deploy. Note it's now `async` — update call sites accordingly.

### 6.7 Field Renderer Visitor Registry

```typescript
// packages/shared/ui/field-renderers/registry.ts
type Renderer = React.ComponentType<{ field: FieldConfig<any>; value: any; onChange: (v: any) => void }>;
const registry = new Map<FieldKind, Renderer>();

export function registerFieldRenderer(kind: FieldKind, component: Renderer) {
  registry.set(kind, component);
}
export function FieldRenderer({ field, value, onChange }: { field: FieldConfig<any>; value: any; onChange: (v: any) => void }) {
  const Component = registry.get(field.kind);
  if (!Component) throw new Error(`No renderer registered for field kind "${field.kind}"`);
  return <Component field={field} value={value} onChange={onChange} />;
}
```

```typescript
// packages/shared/ui/field-renderers/builtins.ts — registered once, at app bootstrap
registerFieldRenderer("text", TextInput);
registerFieldRenderer("number", NumberInput);
registerFieldRenderer("select", SelectInput);
registerFieldRenderer("date", DateInput);
registerFieldRenderer("boolean", CheckboxInput);
```

A new field kind is one component + one `registerFieldRenderer` call. `DataForm`/`DataTable` (§4.8) never change.

### 6.8 CQRS-lite read models

```typescript
// packages/features/wallet/readModels/wallet-summary.selector.ts
import { createSelector } from "@reduxjs/toolkit";
export const selectWalletSummary = createSelector(
  [wallet.selectors.selectAll],
  (wallets) => ({ total: wallets.reduce((s, w) => s + w.balance, 0), count: wallets.length })
);
```

For genuinely heavy list/search/reporting views, back the read model with React Query or RTK Query hitting a read-optimized endpoint instead of deriving from the write-side store — full CQRS rather than "lite."

### 6.9 Workflow Engine

**Step definitions as data:**

```typescript
// packages/core/workflow-engine/step.types.ts
export interface WorkflowContext { vars: Record<string, unknown>; }

export interface StepConfig {
  id: string;
  type: string;   // "callEntity" | "evaluateRules" | "callAI" | "branch" | "parallel" | "humanApproval" | ...
  config: Record<string, unknown>;
  next?: string | { onSuccess: string; onFailure: string } | { branches: Record<string, string> };
}

export interface WorkflowDefinition {
  id: string; name: string; startAt: string;
  steps: Record<string, StepConfig>;
}
```

**Step registry — same Visitor shape as field renderers and async checkers, reused a third time:**

```typescript
// packages/core/workflow-engine/step-registry.ts
type StepResult = { output: unknown; outcome: "success" | "failure" };
type StepExecutor = (config: Record<string, unknown>, ctx: WorkflowContext) => Promise<StepResult>;

const registry = new Map<string, StepExecutor>();
export function registerStep(type: string, executor: StepExecutor) { registry.set(type, executor); }
export function getStepExecutor(type: string): StepExecutor {
  const fn = registry.get(type);
  if (!fn) throw new Error(`No step executor registered for type "${type}"`);
  return fn;
}
```

**Built-in step types, including branch + parallel for real DAG shape:**

```typescript
// packages/core/workflow-engine/builtin-steps.ts
import { resolveRules } from "@core/rules-engine/evaluate";
import { httpClient } from "@core/http/http-client";

registerStep("evaluateRules", async (config, ctx) => {
  const winners = await resolveRules(config.rules as Rule[], { ...(ctx.vars as any) });
  return { output: winners.map((r) => r.effect), outcome: "success" };
});

registerStep("callEntity", async (config, ctx) => {
  const { entity, op, payload } = config as any;
  const result = await registeredEntities[entity].adapter[op](payload);
  return { output: result, outcome: "success" };
});

registerStep("callAI", async (config, ctx) => {
  // thin client only — durable execution, tool-call retries, and the agent loop itself
  // live server-side (Temporal or similar). This traces the round trip; it does NOT
  // reimplement agent orchestration in the browser — see §11.
  const { data } = await httpClient.post(config.endpoint as string, { input: ctx.vars });
  return { output: data, outcome: "success" };
});

registerStep("branch", async (config, ctx) => {
  const winners = await resolveRules(config.rules as Rule[], { ...(ctx.vars as any) });
  return { output: winners[0]?.effect ?? "default", outcome: "success" };
});

registerStep("parallel", async (config, ctx) => {
  await Promise.all((config.stepIds as string[]).map((id) => runStep(id, ctx))); // each still gets its own span
  return { output: null, outcome: "success" };
});

registerStep("humanApproval", (config) => awaitApprovalSignal(config.approvalId as string));
// ^ resolves when a UI component dispatches an approval action — pair with a state
//   machine (§6.4) driving the approval screen itself
```

**Runner — root span per workflow, child span per step:**

```typescript
// packages/core/workflow-engine/run-workflow.ts
import { tracer } from "@core/tracing/tracer";
import { getStepExecutor } from "./step-registry";
import type { WorkflowDefinition, WorkflowContext, StepConfig } from "./step.types";

function nextStepId(step: StepConfig, outcome: "success" | "failure", output: unknown): string | undefined {
  if (typeof step.next === "string") return step.next;
  if (!step.next) return undefined;
  if ("branches" in step.next) return step.next.branches[String(output)];
  return outcome === "success" ? step.next.onSuccess : step.next.onFailure;
}

export async function runWorkflow(def: WorkflowDefinition, ctx: WorkflowContext) {
  return tracer.startActiveSpan(`workflow.${def.name}`, async (rootSpan) => {
    let currentId: string | undefined = def.startAt;
    while (currentId) {
      const step = def.steps[currentId];
      const executor = getStepExecutor(step.type);
      const result = await tracer.startActiveSpan(`step.${step.type}:${step.id}`, async (span) => {
        span.setAttribute("step.id", step.id);
        try {
          const r = await executor(step.config, ctx);
          span.setAttribute("step.outcome", r.outcome);
          return r;
        } finally { span.end(); }
      });
      currentId = nextStepId(step, result.outcome, result.output);
    }
    rootSpan.end();
  });
}
```

### 6.10 Surfacing trace IDs to users/support

```typescript
// packages/shared/lib/current-trace-id.ts
import { trace } from "@opentelemetry/api";
export function currentTraceId(): string | undefined {
  return trace.getActiveSpan()?.spanContext().traceId;
}
```

```tsx
toast.error(`Something went wrong. Reference: ${currentTraceId()?.slice(0, 8)}`);
```

Support pastes that ID into the trace backend and lands directly on the failing request's full waterfall.

---

## 7. Wiring One Feature End-to-End

```typescript
// packages/features/<feature>/index.ts
import { createEntityAdapter } from "@core/data-driven/create-entity-adapter";
import { withTracing, withCircuitBreaker, withCache, withRetry } from "@core/data-driven/adapter-decorators";
import { registerEntity } from "@core/data-driven/register-entity";
import { featureSchema } from "./schema/<feature>.schema";     // includes fromApi/toApi transform ops — §5.3
import { featureRules } from "./rules/<feature>.rules";
import { featureMachine } from "./machines/<feature>.machine";
import { automationWorkflow } from "./workflows/<feature>-automation.workflow";

// tracing outermost — the span covers the full call, including retry backoff and cache-miss latency
const adapter = withTracing(
  withCircuitBreaker(withCache(withRetry(createEntityAdapter(featureSchema)))),
  featureSchema.name
);

export const feature = registerEntity(featureSchema, adapter);
export { featureRules, featureMachine, automationWorkflow };
```

Fifteen lines: fully-wired CRUD, contract-safe (JSON mapping + zod validation), resilient, traced end-to-end, rule-aware, and workflow-capable. Everything upstream of this file is written exactly once in `core/` and shared by every `<feature>` you add — this file is the actual "minimum effort" unit of work per new feature.

---

## 8. Trace Waterfall — What One Click Produces

This is the payoff of §6.1–6.2, §6.3, §6.4, and §6.9 wired together — one user action, one trace:

```
User clicks "Withdraw"
└─ span: withdrawal.transition  (state: idle → validating)        [state machine, §6.4]
   └─ span: workflow.withdrawal-automation                        [workflow runner, §6.9]
      ├─ span: rules.evaluate  (rules.matched_ids=w1,w2,w3)        [rules engine, §6.3]
      │   └─ span: rules.async.kycLiveCheck                       [async checker, §6.3.1]
      ├─ span: step.evaluateRules:check-limits
      └─ span: step.callEntity:debit-wallet
          └─ span: wallet.update                                  [withTracing, §6.2]
              └─ (cache miss → retry x1 → circuit still closed)
                  └─ [BACKEND SPAN] POST /api/wallet/:id           (same traceparent — one trace, two services)
```

"Why was this withdrawal denied" or "why was it stuck for 40 seconds" is one trace-ID lookup, not five log searches across five systems.

---

## 9. Complete Design Pattern Catalog

| Pattern | Category | Lives in | Problem it solves |
|---|---|---|---|
| Port & Adapter (Hexagonal) | Structural | `ports/`, `adapters/` | swap infra without touching business logic |
| Anti-corruption layer | Structural | `json-map.ts` (`fromApi`/`toApi`) + zod `.parse()` | backend contract drift (renamed fields, string-typed numbers, missing columns) stops at the seam, as data, not per-entity code |
| Decorator | Structural | `adapter-decorators.ts` | retry/cache/circuit-breaking/tracing written once, applied everywhere |
| Pipeline / Transform-as-data | Structural | `list-transform.ts`, `json-map.ts` | list shaping (filter/sort/paginate) and JSON mapping become declarative op arrays instead of ad hoc chains repeated per feature |
| Facade | Structural | `core/http/http-client.ts` | one client surface hides fetch details, auto-traced |
| Proxy | Structural | `withCache` decorator | transparent request caching/dedup |
| Factory | Creational | `create-entity-*.ts` | generate adapter/saga/slice from schema |
| Builder | Creational | rule/machine composition | fluent construction of complex rule sets |
| Dependency Injection | Creational | `registerEntity()`, saga factories | swappable, mockable wiring, no hardcoded `new` |
| Strategy | Behavioral | rule `effect` consumed as branching strategy | swap behavior by data, not by editing code |
| Specification | Behavioral | `RuleCondition` and/or/not composition | compose business rules declaratively |
| Chain of Responsibility | Behavioral | saga/rule/workflow-step ordering | ordered checks: auth → rate-limit → validate → execute |
| State Machine | Behavioral | `machines/*.machine.ts` | explicit states/transitions instead of nested conditionals |
| **Visitor / Registry (reused 3×)** | Behavioral | `field-renderers/registry.ts`, `async-checkers.ts`, `workflow-engine/step-registry.ts` | one extensibility shape — `Map` + `registerX()` — solves field rendering, live rule conditions, *and* workflow steps. Learn it once, apply it three times. |
| Observer / Pub-Sub | Behavioral | `event-bus` | cross-feature effects without cross-feature imports |
| Command | Behavioral | dispatched actions | serializable actions enable offline queue, undo, audit log |
| CQRS | Architectural | `state/` (write) vs `readModels/` (read) | reads don't contend with or duplicate write-side logic |
| Saga (orchestration) | Architectural | generated + `overrides/` sagas | coordinate async workflows, retries, cancellation |
| Feature Flags / Progressive Delivery | Architectural | `core/feature-flags` | ship many variants without a new code path per variant |
| Workflow Engine (DAG-as-data) | Architectural | `core/workflow-engine` | define multi-step processes as data; branch/parallel/human-approval as first-class step types |
| Distributed Tracing | Observability | `core/tracing`, every decorator/hook | one waterfall across click → saga → rules → state → workflow → backend |
| Micro-frontends / Module Federation | Org-scale | separate `apps/` per team, if/when needed | independent deploy cadence across many teams |
| Circuit Breaker + Bulkhead | Resilience | `adapter-decorators.ts` | one flaky dependency doesn't cascade-fail the app |
| Edge / ISR / PPR rendering | Infra-scale | Next.js route segment config | serve massive concurrent read traffic from cache/edge |

The **Visitor/Registry row** and the **Pipeline/Transform row** are the two biggest leverage points in the catalog: the first is one ~10-line shape reused three times for extensibility; the second is one ~15-line reducer reused for both list shaping and JSON mapping. Master those two shapes and most future extension points in this architecture are free.

---

## 10. Domain Mapping Cheat Sheet

`<feature>` is a placeholder throughout — nothing in §3–§8 is domain-specific. Here's how it maps onto common domains:

| Domain | `<feature>` becomes | Rules complexity | State machine | Workflow steps |
|---|---|---|---|---|
| Work orders | `work-order` | assignment/SLA/escalation, priority-ranked | `open → assigned → in-progress → done/cancelled` | dispatch automation, escalation on SLA breach |
| Sales | `deal` | discount/approval rules composed from tenant + global | `lead → qualified → proposal → negotiation → closed` | quote-to-cash automation |
| Automations (the builder itself) | `automation-definition` | trigger-condition rules | `queued → running → done/failed` | this IS the workflow engine, self-hosted |
| AI workflows | `agent-run` | routing/guardrail rules, often async (safety checks) | `planning → executing → reviewing → done` | multi-step tool calls, human-approval gates |

---

## 11. Scope Boundaries — What This Does Not Solve

Two boundaries worth stating plainly so you don't over-build or under-provision elsewhere:

**Codebase scale vs. traffic scale.** Everything above keeps the *codebase* scalable — hundreds of features, many engineers, low coupling, fast CI, minimal repetition. That's what design patterns govern. Serving genuinely massive *traffic* (millions of concurrent requests) is overwhelmingly a CDN/edge/backend/database problem — sharding, load balancing, edge caching. The frontend's job there is narrower: be stateless per-request, cacheable, and edge-renderable via Next.js's route-segment `revalidate`/ISR, streaming SSR, and per-feature code-splitting, so the origin does as little work as possible per request. Keep the two separate — solve traffic-scale problems in the infra layer and codebase-scale problems in the patterns above.

**The workflow engine is not a durable execution engine.** §6.9 composes what runs and in what order, renders progress, and traces every step. It has no persistence across page reloads, no distributed retries, no exactly-once guarantees. For workflows that must survive a closed tab or a crashed server — which is most of "millions of complex AI workflow runs" — that execution belongs server-side. A durable orchestrator like Temporal (§12) is the standard tool for exactly this. The frontend's `callAI`/`callEntity` steps stay thin clients that kick off and poll/stream that backend execution; this layer's job is the human-facing half — defining the step sequence as data, rendering live progress, handling approval gates — not re-implementing a workflow engine in the browser.

---

## 12. Durable Execution — Making the Workflow Engine Actually Durable

§6.9's `runWorkflow` is fine for short, UI-only sequences (a wizard, a multi-step form) but has no persistence — close the tab and it's gone. For anything that must survive a crash, a closed tab, or needs real retry/backoff at scale, the workflow moves server-side into Temporal, and the frontend becomes a thin client that starts it and streams status.

**Frontend — replaces in-browser execution for anything durable:**

```typescript
// packages/core/workflow-engine/run-durable-workflow.ts
import { httpClient } from "@core/http/http-client";
import { tracer } from "@core/tracing/tracer";

export async function startDurableWorkflow(workflowType: string, input: Record<string, unknown>) {
  return tracer.startActiveSpan(`durable.${workflowType}.start`, async (span) => {
    const { data } = await httpClient.post(`/api/workflows/${workflowType}/start`, input);
    span.setAttribute("workflow.id", data.workflowId);
    span.end();
    return data.workflowId as string;
  });
}

export function subscribeDurableWorkflow(workflowId: string, onUpdate: (status: unknown) => void) {
  const es = new EventSource(`/api/workflows/${workflowId}/stream`);
  es.onmessage = (e) => onUpdate(JSON.parse(e.data));
  return () => es.close();
}
```

**Rule of thumb:** `runWorkflow` (§6.9, in-memory) for ephemeral UI sequences; `startDurableWorkflow` (above) for anything that represents real business state — dispatch, quote-to-cash, an AI agent run. The backend implementation lives in §15.5.

---

## 13. Governance, RBAC & Audit Logging

Three concerns, and all three reuse engines you already have rather than introducing new ones:

**RBAC — permissions as data, reusing the rules engine:**

```typescript
// packages/core/rbac/permission.types.ts
import type { RuleCondition } from "@core/rules-engine/rule.types";

export interface Permission {
  id: string;
  resource: string;              // "wallet", "rules:wallet", "flag:*"
  action: "read" | "create" | "update" | "delete" | "approve";
  when?: RuleCondition;          // e.g. only within own tenant/region — same engine as §6.3
}
```

```typescript
// packages/core/rbac/can.ts
import { resolveRules } from "@core/rules-engine/evaluate";
import type { Permission } from "./permission.types";
import type { Rule, RuleContext } from "@core/rules-engine/rule.types";

function matchResource(pattern: string, resource: string): boolean {
  return pattern === "*" || pattern === resource || (pattern.endsWith(":*") && resource.startsWith(pattern.slice(0, -1)));
}

export async function can(permissions: Permission[], resource: string, action: string, ctx: RuleContext): Promise<boolean> {
  const applicable = permissions.filter((p) => matchResource(p.resource, resource) && p.action === action);
  if (!applicable.length) return false;
  if (applicable.some((p) => !p.when)) return true;
  const asRules: Rule[] = applicable.map((p) => ({ id: p.id, description: p.resource, when: p.when!, effect: "allow" }));
  return (await resolveRules(asRules, ctx)).length > 0;
}
```

**Governance for rule/flag changes — reuses the workflow engine's `humanApproval` step (§6.9):** give every `Rule` and `FlagConfig` a `status: "draft" | "approved"` and `approvedBy` field. Only `approved` rules feed `resolveRules` in production; a `draft` rule runs in a shadow evaluation for review. Promoting draft → approved is itself a small workflow definition (`evaluateRules` → `humanApproval` → flip status) — no new system, same engine as everything else in this doc.

**Audit logging — every mutation, tied to the trace ID that's already flowing through the system:**

```typescript
// packages/core/audit/audit-log.ts
import { httpClient } from "@core/http/http-client";
import { currentTraceId } from "@shared/lib/current-trace-id";

export interface AuditEntry { actorId: string; action: string; resource: string; before?: unknown; after?: unknown; }

export async function recordAudit(entry: AuditEntry) {
  await httpClient.post("/api/audit-log", { ...entry, traceId: currentTraceId(), at: new Date().toISOString() });
}
```

Call `recordAudit` from the saga's `createOne`/`removeOne` (§4.6) right next to the existing `eventBus.emit` — same spot, same trace context, one more line. The backend audit store (§15.6) is append-only by construction: no update/delete function is ever exposed on that module.

---

## 14. Security Hardening Checklist

| Concern | Where enforced | How |
|---|---|---|
| Authentication | `core/security/auth.py` (backend) | JWT/OAuth2 verified server-side; populates the `RuleContext`/`ctx` used by rules, RBAC, and audit — never trust a frontend-supplied identity |
| Authorization | RBAC `can()` (§13) | Every mutating route checks permissions **server-side** before touching data. A frontend-only permission check is a UX nicety, not security. |
| Audit | `audit_log.py` (§15.6) | Append-only, trace-ID linked, no update/delete method exposed on the module |
| Input validation | zod (frontend, §4.1) / Pydantic (backend, §15.2) | Same anti-corruption boundary as the JSON transform layer (§5.2) — malformed input never reaches business logic |
| PII exposure | Extend `JsonMapOp`/transform ops with a `mask` op | `{ op: "mask", field: "ssn", show: 4 }` — apply in `DataTable`/list read models, never store masked data, only display it masked |
| Rate limiting | `core/security/rate_limit.py` + edge/gateway | Non-optional at billions-of-users scale — enforce at the edge, not just in-app |
| CORS / trace leakage | `FetchInstrumentation` origin allowlist (§6.1, frontend) + FastAPI CORS middleware (backend) | Never wildcard either — a wildcarded `propagateTraceHeaderCorsUrls` leaks trace headers to third parties |
| Secrets | Backend env vars only | Anything under `NEXT_PUBLIC_*` in Next.js is public by design — never put a real secret there |
| Supply chain | CI SCA/dependency scanning, least-privilege service accounts for Temporal workers | Standard hygiene, but easy to skip under deadline pressure — don't |

---

## 15. Python Backend — Complete Mirror Architecture

Same depth, same "small generic engine + data" philosophy, same file-for-file shape as the frontend — FastAPI + Pydantic + SQLAlchemy + Temporal Python SDK + OpenTelemetry Python.

### 15.1 Folder structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI app, mounts routers, OTEL instrumentation
│   ├── core/
│   │   ├── tracing/
│   │   │   └── tracer.py                # OTEL SDK setup, auto-instruments FastAPI + httpx
│   │   ├── data_driven/
│   │   │   ├── entity_schema.py         # Pydantic-based EntitySchema — mirrors §4.1
│   │   │   ├── transform.py             # transform_list / map_json — same ops as §5, ported 1:1
│   │   │   ├── repository.py            # generic SQLAlchemy repository factory — mirrors §4.4
│   │   │   ├── decorators.py            # with_retry / with_cache / with_circuit_breaker / with_tracing — mirrors §6.2
│   │   │   └── registry.py              # registered_entities — mirrors feature-registry.ts
│   │   ├── rules_engine/
│   │   │   ├── types.py                 # mirrors §6.3
│   │   │   ├── async_checkers.py
│   │   │   ├── evaluate.py              # resolve_rules — priority + deny-override + async, traced
│   │   │   └── compose.py
│   │   ├── rbac/
│   │   │   ├── permission_types.py      # mirrors §13
│   │   │   └── can.py
│   │   ├── audit/
│   │   │   └── audit_log.py             # append-only, trace-ID linked — mirrors §13
│   │   ├── workflow_engine/
│   │   │   ├── activities.py            # Temporal activities — evaluateRules / callEntity / callAI / ...
│   │   │   ├── workflows.py             # @workflow.defn — durable, this closes the §11 gap for real
│   │   │   └── worker.py                # Temporal worker process entrypoint
│   │   ├── event_bus/
│   │   │   └── event_bus.py             # pub/sub, or a Redis/Kafka-backed adapter at scale
│   │   └── security/
│   │       ├── auth.py                  # JWT/OAuth2 verification, builds RuleContext
│   │       └── rate_limit.py
│   ├── features/
│   │   └── <feature>/
│   │       ├── schema.py                # Pydantic model + from_db/to_db transform ops
│   │       ├── rules.py
│   │       ├── permissions.py           # this feature's Permission[] — §13
│   │       ├── router.py                # FastAPI router: RBAC check → repository call → audit log
│   │       └── tests/
│   ├── db/
│   │   ├── models.py                    # SQLAlchemy models, incl. AuditEntry
│   │   └── session.py
│   └── config/
│       └── settings.py                  # pydantic-settings, env schema
├── alembic/                              # migrations
├── pyproject.toml
└── docker-compose.yml                    # app + postgres + temporal + otel-collector
```

### 15.2 Entity Schema — Pydantic mirror of §4.1

```python
# app/core/data_driven/entity_schema.py
from typing import Optional
from pydantic import BaseModel

class FieldConfig(BaseModel):
    key: str
    label: str
    kind: str          # "text" | "number" | "select" | "date" | "boolean"
    required: bool = False

class EntitySchema(BaseModel):
    name: str
    table: str
    fields: list[FieldConfig]
    model: type[BaseModel]      # the runtime anti-corruption boundary, same role as zod on the frontend
    from_db: list[dict] = []    # DB row -> API shape, same op vocabulary as §5.2
    to_db: list[dict] = []      # API shape -> DB row
```

### 15.3 Transform Layer — ported 1:1 from §5, same ops, same shape

```python
# app/core/data_driven/transform.py
def _get(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    return cur

def _set(obj: dict, path: str, value) -> None:
    parts = path.split(".")
    cur = obj
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value

_COERCERS = {"string": str, "number": float, "boolean": bool}

def map_json(item: dict, ops: list[dict]) -> dict:
    out = dict(item)
    for op in ops:
        kind = op["op"]
        if kind == "rename":
            _set(out, op["to"], _get(out, op["from"]))
            if op["from"] != op["to"]:
                out.pop(op["from"], None)
        elif kind == "pick":
            out = {f: _get(out, f) for f in op["fields"]}
        elif kind == "omit":
            out = {k: v for k, v in out.items() if k not in op["fields"]}
        elif kind == "default" and _get(out, op["field"]) is None:
            _set(out, op["field"], op["value"])
        elif kind == "coerce":
            val = _get(out, op["field"])
            if val is not None:
                _set(out, op["field"], _COERCERS[op["to"]](val))
    return out

def _matches(value, match: str, target) -> bool:
    ops = {
        "eq": lambda: value == target, "neq": lambda: value != target,
        "in": lambda: value in (target or []),
        "gt": lambda: value is not None and value > target, "lt": lambda: value is not None and value < target,
        "gte": lambda: value is not None and value >= target, "lte": lambda: value is not None and value <= target,
        "contains": lambda: str(target).lower() in str(value or "").lower(),
    }
    return ops.get(match, lambda: False)()

def transform_list(items: list[dict], ops: list[dict]) -> list[dict]:
    result = items
    for op in ops:
        kind = op["op"]
        if kind == "filter":
            result = [i for i in result if _matches(_get(i, op["field"]), op["match"], op["value"])]
        elif kind == "search":
            q = op["query"].lower()
            result = [i for i in result if any(q in str(_get(i, f) or "").lower() for f in op["fields"])]
        elif kind == "sort":
            result = sorted(result, key=lambda i: _get(i, op["field"]), reverse=(op.get("dir") == "desc"))
        elif kind == "paginate":
            start = (op["page"] - 1) * op["pageSize"]
            result = result[start : start + op["pageSize"]]
    return result
```

### 15.4 Repository Factory — mirrors §4.4's adapter

```python
# app/core/data_driven/repository.py
from sqlalchemy import select
from .transform import map_json
from .entity_schema import EntitySchema

class Repository:
    def __init__(self, schema: EntitySchema, table, session_factory):
        self.schema, self.table, self.session_factory = schema, table, session_factory

    def _from_db(self, row: dict) -> dict:
        return map_json(row, self.schema.from_db) if self.schema.from_db else row

    def _to_db(self, entity: dict) -> dict:
        return map_json(entity, self.schema.to_db) if self.schema.to_db else entity

    async def list(self) -> list[dict]:
        async with self.session_factory() as s:
            rows = (await s.execute(select(self.table))).scalars().all()
            return [self.schema.model(**self._from_db(vars(r))).model_dump() for r in rows]

    async def create(self, payload: dict) -> dict:
        async with self.session_factory() as s:
            row = self.table(**self._to_db(payload))
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return self.schema.model(**self._from_db(vars(row))).model_dump()
    # get / update / remove follow the identical shape — omitted for brevity
```

### 15.5 Rules Engine — mirrors §6.3

```python
# app/core/rules_engine/types.py
from typing import Literal, Optional
from pydantic import BaseModel

class RuleCondition(BaseModel):
    op: str
    field: Optional[str] = None
    value: Optional[object] = None
    values: Optional[list] = None
    conditions: Optional[list["RuleCondition"]] = None
    condition: Optional["RuleCondition"] = None
    resolver: Optional[str] = None

class Rule(BaseModel):
    id: str
    description: str
    when: RuleCondition
    effect: str
    priority: int = 0
    category: Optional[Literal["allow", "deny", "modify"]] = None
```

```python
# app/core/rules_engine/evaluate.py
from opentelemetry import trace
from .async_checkers import get_async_checker
from .types import RuleCondition, Rule

tracer = trace.get_tracer("backend")

def _get(ctx: dict, path: str):
    cur = ctx
    for p in path.split("."):
        cur = cur.get(p) if isinstance(cur, dict) else None
    return cur

async def _eval(cond: RuleCondition, ctx: dict) -> bool:
    op = cond.op
    if op == "eq":  return _get(ctx, cond.field) == cond.value
    if op == "in":  return _get(ctx, cond.field) in (cond.values or [])
    if op == "gt":  return _get(ctx, cond.field) > cond.value
    if op == "lt":  return _get(ctx, cond.field) < cond.value
    if op == "gte": return _get(ctx, cond.field) >= cond.value
    if op == "lte": return _get(ctx, cond.field) <= cond.value
    if op == "and": return all([await _eval(c, ctx) for c in (cond.conditions or [])])
    if op == "or":  return any([await _eval(c, ctx) for c in (cond.conditions or [])])
    if op == "not": return not await _eval(cond.condition, ctx)
    if op == "asyncCheck":
        with tracer.start_as_current_span(f"rules.async.{cond.resolver}"):
            return await get_async_checker(cond.resolver)(ctx)
    return False

async def resolve_rules(rules: list[Rule], ctx: dict) -> list[Rule]:
    with tracer.start_as_current_span("rules.evaluate") as span:
        matched = [r for r in rules if await _eval(r.when, ctx)]
        denies = [r for r in matched if r.category == "deny"]
        winners = denies if denies else sorted(matched, key=lambda r: -r.priority)
        span.set_attribute("rules.matched_ids", ",".join(r.id for r in matched))
        span.set_attribute("rules.winning_ids", ",".join(r.id for r in winners))
        return winners
```

### 15.6 RBAC + Audit Log — server-side enforcement, mirrors §13

```python
# app/core/rbac/can.py
from fnmatch import fnmatch
from app.core.rules_engine.evaluate import resolve_rules
from app.core.rules_engine.types import Rule

async def can(permissions: list, resource: str, action: str, ctx: dict) -> bool:
    applicable = [p for p in permissions if fnmatch(resource, p.resource) and p.action == action]
    if not applicable:
        return False
    if any(p.when is None for p in applicable):
        return True
    as_rules = [Rule(id=p.id, description=p.resource, when=p.when, effect="allow") for p in applicable]
    return len(await resolve_rules(as_rules, ctx)) > 0
```

```python
# app/core/audit/audit_log.py
from datetime import datetime, timezone
from opentelemetry import trace
from app.db.session import async_session
from app.db.models import AuditEntry

async def record_audit(actor_id: str, action: str, resource: str, before=None, after=None) -> None:
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x") if span else None
    async with async_session() as s:
        s.add(AuditEntry(actor_id=actor_id, action=action, resource=resource,
                          before=before, after=after, trace_id=trace_id, at=datetime.now(timezone.utc)))
        await s.commit()
# No update/delete exported from this module — append-only by construction, not just by convention.
```

```python
# app/features/wallet/router.py — RBAC check -> repository -> audit, in that order, every time
from fastapi import APIRouter, Depends, HTTPException
from app.core.security.auth import get_current_ctx
from app.core.rbac.can import can
from app.core.audit.audit_log import record_audit
from .schema import wallet_repository
from .permissions import wallet_permissions

router = APIRouter(prefix="/api/wallets")

@router.post("/")
async def create_wallet(payload: dict, ctx: dict = Depends(get_current_ctx)):
    if not await can(wallet_permissions, "wallet", "create", ctx):
        raise HTTPException(403, "forbidden")
    result = await wallet_repository.create(payload)
    await record_audit(ctx["user"]["id"], "create", "wallet", after=result)
    return result
```

### 15.7 Durable Workflow Engine — Temporal, closing the §11/§12 gap for real

```python
# app/core/workflow_engine/activities.py
from temporalio import activity
from app.core.rules_engine.evaluate import resolve_rules
from app.core.data_driven.registry import registered_entities

@activity.defn(name="evaluateRules")
async def evaluate_rules_activity(config: dict, ctx: dict) -> dict:
    winners = await resolve_rules(config["rules"], ctx)
    return {"output": [r.effect for r in winners], "outcome": "success"}

@activity.defn(name="callEntity")
async def call_entity_activity(config: dict, ctx: dict) -> dict:
    repo = registered_entities[config["entity"]].repository
    result = await getattr(repo, config["op"])(config.get("payload"))
    return {"output": result, "outcome": "success"}
```

```python
# app/core/workflow_engine/workflows.py
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class AutomationWorkflow:
    @workflow.run
    async def run(self, definition: dict, ctx: dict) -> dict:
        current_id = definition["startAt"]
        while current_id:
            step = definition["steps"][current_id]
            result = await workflow.execute_activity(
                step["type"], args=[step["config"], ctx],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            current_id = _next_step_id(step, result)
        return ctx
```

```python
# app/core/workflow_engine/worker.py — separate long-running process from the FastAPI app
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from .workflows import AutomationWorkflow
from .activities import evaluate_rules_activity, call_entity_activity

async def main():
    client = await Client.connect("temporal:7233")
    worker = Worker(client, task_queue="automation-queue",
                     workflows=[AutomationWorkflow],
                     activities=[evaluate_rules_activity, call_entity_activity])
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# app/features/automation/router.py — what §12's startDurableWorkflow/subscribeDurableWorkflow call
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from temporalio.client import Client
from app.core.workflow_engine.workflows import AutomationWorkflow
import asyncio

router = APIRouter(prefix="/api/workflows")

@router.post("/{workflow_type}/start")
async def start_workflow(workflow_type: str, payload: dict):
    client = await Client.connect("temporal:7233")
    handle = await client.start_workflow(
        AutomationWorkflow.run, args=[payload["definition"], payload["ctx"]],
        id=f"{workflow_type}-{payload['ctx'].get('id')}", task_queue="automation-queue",
    )
    return {"workflowId": handle.id}

@router.get("/{workflow_id}/stream")
async def stream_workflow(workflow_id: str):
    async def event_gen():
        client = await Client.connect("temporal:7233")
        handle = client.get_workflow_handle(workflow_id)
        while True:
            desc = await handle.describe()
            yield f"data: {desc.status.name}\n\n"
            if desc.status.name in ("COMPLETED", "FAILED", "TERMINATED"):
                break
            await asyncio.sleep(2)
    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

This is real durability: survives a crashed pod, a closed browser tab, or a restarted worker, with retries and exactly-once activity execution — the thing §11 flagged as missing.

---

## 16. Compliance Primitives — Encryption, Erasure, Consent, Residency

Architecture gives you the *mechanisms* compliance frameworks require — it isn't compliance itself (that also needs legal/policy work, DPAs, and third-party audits). These ten items are the code-level pieces still missing from §12–§15, each reusing an engine you already have rather than introducing a new one.

### 16.1 Encryption — at rest, and a transform op for app-level PII

DB-level: enable `pgcrypto` in Postgres and encrypt sensitive columns natively. App-level, for fields that must be encrypted before they ever reach the DB layer (e.g. cross-region replicated data): extend the transform vocabulary from §5.2/§15.3 with one more op.

```python
# app/core/data_driven/transform.py (addition)
from cryptography.fernet import Fernet
_fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)  # from secrets manager, §16.7 — never a literal

# add to map_json's op dispatch:
        elif kind == "encrypt":
            val = _get(out, op["field"])
            if val is not None:
                _set(out, op["field"], _fernet.encrypt(str(val).encode()).decode())
        elif kind == "decrypt":
            val = _get(out, op["field"])
            if val is not None:
                _set(out, op["field"], _fernet.decrypt(val.encode()).decode())
```

```python
# usage in a schema's to_db/from_db — same declarative shape as every other mapping
to_db = [{"op": "encrypt", "field": "ssn"}]
from_db = [{"op": "decrypt", "field": "ssn"}]
```

### 16.2 Right to erasure (GDPR Art. 17) — cascading purge, not a raw DELETE

Erasure must touch the DB row, the audit trail (redact, don't delete — §16.5), the event bus history if persisted, and any Temporal workflow history referencing the user.

```python
# app/core/data_driven/purge.py
from app.core.data_driven.registry import registered_entities
from app.core.audit.audit_log import redact_actor
from app.core.event_bus.event_bus import purge_actor_events

async def purge_subject(user_id: str) -> None:
    for name, entity in registered_entities.items():
        rows = await entity.repository.list_by_owner(user_id)   # each schema declares its owner field
        for row in rows:
            await entity.repository.remove(row["id"])
    await redact_actor(user_id)          # §16.5 — overwrites PII fields in place, keeps the audit row
    await purge_actor_events(user_id)
```

Wire this as a `humanApproval`-gated workflow step (§6.9/§13), not a bare endpoint — erasure requests should go through the same governance path as any other sensitive action, with a record of who approved it.

### 16.3 Consent tracking — a rule, not a boolean scattered through the codebase

```python
# app/features/consent/schema.py
class Consent(BaseModel):
    user_id: str
    purpose: str          # "marketing", "analytics", "third_party_sharing"
    granted: bool
    at: datetime
```

Enforced the same way every other business rule is enforced — as a condition in `RuleContext`, not an `if` scattered across every email/analytics call site:

```python
{ "id": "c1", "description": "Only send marketing email with active consent",
  "when": { "op": "eq", "field": "user.consent.marketing", "value": True },
  "category": "allow", "effect": "send.marketing" }
```

### 16.4 PII masking/tokenization for display — extends §5.2/§15.3 directly

```python
# add to map_json's op dispatch (Python) / mapJson's switch (TypeScript, mirror in json-map.ts)
        elif kind == "mask":
            val = str(_get(out, op["field"]) or "")
            show = op.get("show", 4)
            _set(out, op["field"], "*" * max(0, len(val) - show) + val[-show:])
```

```typescript
{ op: "mask", field: "ssn", show: 4 }   // in a DataTable's schema.fromApi — masked at the boundary, never unmasked client-side
```

Apply in read models and `DataTable`/list views (§4.8) — never in the write path, and never log the unmasked value (§16.9).

### 16.5 Immutable audit log — enforced by the database, not app discipline

```sql
-- alembic migration
REVOKE UPDATE, DELETE ON audit_entry FROM app_user;
GRANT INSERT, SELECT ON audit_entry TO app_user;
```

`redact_actor` (used by §16.2) is the one sanctioned exception — it runs as a privileged migration-style operation, overwriting PII columns in place while leaving the row (and its trace ID) intact, and is itself audited under a separate elevated role.

### 16.6 Session/token security

```python
# app/core/security/auth.py (addition)
ACCESS_TOKEN_TTL = timedelta(minutes=15)     # short-lived
REFRESH_TOKEN_TTL = timedelta(days=14)

async def rotate_refresh_token(old_token: str) -> tuple[str, str]:
    session = await get_session_by_refresh(old_token)
    if session.revoked:
        raise HTTPException(401, "session revoked")
    await revoke_session(session.id)              # one-time use — old token dead the moment it's exchanged
    return issue_token_pair(session.user_id)

@router.post("/sessions/{session_id}/revoke")
async def revoke_session_endpoint(session_id: str, ctx: dict = Depends(get_current_ctx)):
    await revoke_session(session_id)               # lets a user kill a stolen/lost-device session
```

### 16.7 Secrets management — never `.env` in production

```python
# app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    field_encryption_key: str
    database_url: str
    temporal_address: str
    class Config:
        secrets_dir = "/run/secrets"   # mounted from Vault/AWS Secrets Manager/K8s Secrets — not a committed .env
```

### 16.8 Data residency routing

```python
# app/core/data_driven/registry.py (addition)
_REGION_SESSIONS = {"EU": eu_session_factory, "US": us_session_factory}

def session_factory_for(ctx: dict):
    return _REGION_SESSIONS.get(ctx["user"]["region"], _REGION_SESSIONS["US"])
```

Pass `session_factory_for(ctx)` into `Repository` (§15.4) at request time instead of a fixed factory — an EU user's data never touches a US-hosted Postgres instance, decided by the same `ctx` already flowing through rules/RBAC/audit.

### 16.9 Structured logging with PII redaction

```python
# app/core/tracing/tracer.py (addition)
import logging
class RedactPII(logging.Filter):
    _FIELDS = {"ssn", "password", "credit_card"}
    def filter(self, record: logging.LogRecord) -> bool:
        for f in self._FIELDS:
            if hasattr(record, f):
                setattr(record, f, "[REDACTED]")
        return True

logging.getLogger().addFilter(RedactPII())
```

### 16.10 Dependency/vulnerability scanning in CI

```yaml
# .github/workflows/ci.yml (addition)
- name: Python dependency audit
  run: pip-audit -r backend/requirements.txt
- name: JS dependency audit
  run: pnpm audit --audit-level=high
- name: Container image scan
  uses: aquasecurity/trivy-action@master
  with: { image-ref: "myapp:${{ github.sha }}" }
```

Fail the build on high/critical findings — a checklist item that isn't enforced in CI isn't a control, it's a hope.

---

## 17. Production Readiness

A priority table first, then the code. Not everything here is equally urgent — some of it is a correctness bug the moment you run more than one instance, some of it can mature in your first month live.

| Item | Must-have before launch? | Why |
|---|---|---|
| §17.1 Distributed cache/event bus | **Yes** | Silent correctness bug otherwise — the in-memory versions from §6.2/§6.5 stop working correctly the moment you run a second replica |
| §17.2 Idempotency keys | **Yes** | Without it, the retry logic you already built (§6.2) can double-create/double-charge on a retried request |
| §17.3 Multi-tenant row-level security | **Yes** | One missed `WHERE` clause in a repository method becomes a cross-tenant data breach |
| §17.4 Backpressure/load shedding | **Yes** | Prevents one overloaded dependency from cascading into a full outage |
| §17.5 Health checks + graceful shutdown | **Yes** | Kubernetes (or any orchestrator) needs this to route traffic and roll deploys safely |
| §17.6 Schema/version evolution | **Yes, before your first prod schema change** | Otherwise a migration breaks in-flight Temporal workflows and queued events still shaped like the old schema |
| §17.7 Rules/workflow test harness | **Yes** | You explicitly said "very very complex flows" — untested rule conflicts across thousands of rules are silent bugs, not loud ones |
| §17.8 DB pooling, replicas, timeouts | **Yes** | Unpooled connections and un-timed-out queries exhaust Postgres long before you reach "billions" |
| §17.9 Dead letter queues | Recommended at launch | Otherwise a step that exhausts retries just disappears |
| §17.10 API versioning | Recommended at launch | Cheap now, expensive to retrofit once external clients depend on v1 |
| §17.11 Load testing | Do once before go-live, then iterate | One real load test against a staging env sized like prod is non-negotiable |
| §17.12 Canary/flag-gated deploys | Can mature post-launch | Start with a manual rollout %, automate the watch-and-rollback later |
| §17.13 Disaster recovery | Backups at launch, rehearsed restore within month 1 | An untested backup is a hope, not a plan |
| §17.14 SLOs & error budgets | Within month 1 | Needs real traffic data to calibrate meaningfully anyway |

### 17.1 Fixing In-Memory State That Only Works Single-Process

Three pieces of code earlier in this doc use a closure or local variable for state: `withCache` and `withCircuitBreaker` (§6.2), and `EventBus` (§6.5). All three are correct for exactly one process. The moment you run more than one instance behind a load balancer — guaranteed at your scale — each instance has its own private cache and its own private failure counters, and, critically, `EventBus.emit` only reaches handlers registered **in the same process**, silently dropping cross-pod event delivery. This isn't a future scaling concern; it's a correctness bug the moment a second replica exists.

**Cache — Redis-backed:**

```python
# app/core/data_driven/decorators.py (production version of with_cache)
import json
import redis.asyncio as redis
from functools import wraps

_redis = redis.from_url(settings.redis_url)

def with_cache_distributed(ttl_seconds: int = 30):
    def deco(fn):
        @wraps(fn)
        async def wrapper(self, *a, **kw):
            key = f"cache:{self.schema.name}:{fn.__name__}:{a}"
            if (cached := await _redis.get(key)) is not None:
                return json.loads(cached)
            result = await fn(self, *a, **kw)
            await _redis.set(key, json.dumps(result), ex=ttl_seconds)
            return result
        return wrapper
    return deco
```

**Event bus — Redis pub/sub, so every pod's subscribers actually receive the event:**

```python
# app/core/event_bus/event_bus.py (production version)
import json
import redis.asyncio as redis

class DistributedEventBus:
    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url)
        self._handlers: dict[str, list] = {}

    def on(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    async def emit(self, event: str, payload: dict) -> None:
        await self._redis.publish(event, json.dumps(payload))   # reaches every pod, not just this one

    async def start_listening(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe("*")
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            for handler in self._handlers.get(message["channel"].decode(), []):
                await handler(json.loads(message["data"]))

event_bus = DistributedEventBus(settings.redis_url)
```

**Circuit breaker — usually fine as-is.** Per-instance breakers (§6.2) are a defensible, common pattern (each instance protects itself independently); the downside is that one instance may have its circuit open while another keeps hammering a failing dependency. Centralizing via Redis adds a round-trip to every call and a new failure mode (what does the breaker do if Redis itself is slow?). Only centralize this one if you specifically need cluster-wide breaker consensus — don't do it by default.

### 17.2 Idempotency Keys

```python
# app/core/data_driven/idempotency.py
import json

async def with_idempotency_key(key: str, fn, *args, **kwargs):
    if (existing := await _redis.get(f"idem:{key}")) is not None:
        return json.loads(existing)
    result = await fn(*args, **kwargs)
    await _redis.set(f"idem:{key}", json.dumps(result), ex=86_400, nx=True)
    return result
```

```python
# app/features/wallet/router.py (addition)
@router.post("/")
async def create_wallet(payload: dict, idempotency_key: str = Header(...), ctx: dict = Depends(get_current_ctx)):
    if not await can(wallet_permissions, "wallet", "create", ctx):
        raise HTTPException(403, "forbidden")
    return await with_idempotency_key(idempotency_key, wallet_repository.create, payload)
```

Client (frontend saga, §4.6) generates and sends a UUID per logical action, and resends the same key on retry — the server now guarantees exactly-once effect regardless of network retries.

### 17.3 Multi-Tenant Isolation — Enforced by Postgres, Not Just Application Code

```sql
-- alembic migration
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON wallets
  USING (tenant_id = current_setting('app.current_tenant')::text);
```

```python
# app/db/session.py (addition) — set once per request; a bug in a repository method
# can no longer leak cross-tenant rows even if it forgets a WHERE clause
async def scoped_session(tenant_id: str):
    async with async_session() as s:
        await s.execute(text("SET app.current_tenant = :t"), {"t": tenant_id})
        yield s
```

### 17.4 Backpressure & Load Shedding

```python
# app/main.py (addition) — reject new work before the process falls over, rather than queuing until it does
from fastapi import Request, HTTPException

_MAX_CONCURRENT = 5000
_inflight = 0

@app.middleware("http")
async def load_shed(request: Request, call_next):
    global _inflight
    if _inflight >= _MAX_CONCURRENT:
        raise HTTPException(503, "at capacity, retry with backoff")
    _inflight += 1
    try:
        return await call_next(request)
    finally:
        _inflight -= 1
```

Pair this with a Temporal task-queue backlog alarm (queue depth growing faster than workers drain it is the earliest signal of a downstream slowdown).

### 17.5 Health Checks & Graceful Shutdown

```python
# app/main.py (addition)
import signal
from fastapi import HTTPException

_shutting_down = False

@app.get("/healthz")
async def liveness():
    return {"status": "ok"}

@app.get("/readyz")
async def readiness():
    if _shutting_down:
        raise HTTPException(503, "shutting down")
    # also ping DB / redis / temporal here in a real implementation
    return {"status": "ready"}

def handle_sigterm(*_):
    global _shutting_down
    _shutting_down = True   # readyz starts failing -> LB stops routing new traffic; in-flight requests finish naturally

signal.signal(signal.SIGTERM, handle_sigterm)
```

Temporal workflows need no special drain handling here — that's the point of durability (§12/§15.7): if the pod dies mid-step, the workflow resumes elsewhere.

### 17.6 Schema Evolution — So a Migration Doesn't Break In-Flight Data

```python
# app/core/data_driven/entity_schema.py (addition)
class EntitySchema(BaseModel):
    name: str
    version: int = 1          # bump whenever from_db/to_db ops change shape
    ...
```

```python
# app/core/data_driven/repository.py (addition) — tag every row with the schema version it was written under
async def create(self, payload: dict) -> dict:
    async with self.session_factory() as s:
        row = self.table(**self._to_db(payload), schema_version=self.schema.version)
        s.add(row); await s.commit(); await s.refresh(row)
        return self.schema.model(**self._from_db(vars(row))).model_dump()
```

`from_db` dispatches on the row's own `schema_version`, not the current schema's — so rows written before a migration, and Temporal workflow history or queued events still referencing the old shape, keep deserializing correctly during rollout.

### 17.7 Testing Harness for Rules & Workflows at Scale

```python
# tests/test_rules_conflicts.py — property-based: no realistic input should produce
# two "allow" winners disagreeing on the same effect namespace
from hypothesis import given, strategies as st

@given(tier=st.sampled_from(["free", "pro", "enterprise"]), region=st.text(min_size=2, max_size=2))
async def test_no_undefined_winner(tier, region):
    ctx = {"user": {"tier": tier, "region": region, "kycStatus": "verified"}, "now": datetime.utcnow()}
    winners = await resolve_rules(wallet_rules, ctx)
    effects = [w.effect.split(":")[0] for w in winners if w.category != "deny"]
    assert len(effects) == len(set(effects)), f"conflicting rules fired for {ctx}"
```

```python
# tests/test_workflow_snapshot.py — golden-file test: a workflow's step trace for a fixed
# input shouldn't silently change when someone edits builtin-steps.py
async def test_withdrawal_workflow_snapshot(snapshot):
    result = await run_workflow_in_test_env(withdrawal_workflow_def, sample_ctx())
    assert result.step_trace == snapshot
```

At "thousands of rules," this pair of test styles is the difference between a rule conflict surfacing in code review and surfacing as a production incident.

### 17.8 Database: Pooling, Read Replicas, Query Timeouts

```python
# app/db/session.py (addition)
engine = create_async_engine(
    settings.database_url,
    pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=1800,
    connect_args={"command_timeout": 5},   # a hard timeout so one stuck query can't take the pod down with it
)
read_replica_engine = create_async_engine(settings.read_replica_url, pool_size=40)
# route list()/get() to read_replica_engine, create/update/remove to the primary —
# the same read/write split as CQRS-lite (§4.8/§6.8), now at the database layer
```

### 17.9 Dead Letter Queues

```python
# app/core/workflow_engine/workflows.py (addition)
try:
    result = await workflow.execute_activity(
        step["type"], args=[step["config"], ctx],
        start_to_close_timeout=timedelta(minutes=5), retry_policy=RetryPolicy(maximum_attempts=3),
    )
except Exception as e:
    await workflow.execute_activity(
        "sendToDeadLetterQueue", args=[{"step": step, "error": str(e), "ctx": ctx}],
        start_to_close_timeout=timedelta(seconds=30),
    )
    raise
```

A step that exhausts retries goes to a queue/table for manual review instead of vanishing.

### 17.10 API Versioning

```python
# app/main.py (addition)
app.include_router(wallet_router_v1, prefix="/api/v1")
app.include_router(wallet_router_v2, prefix="/api/v2")
# schema.version (§17.6) travels with the entity's storage shape; the API version is the
# outer contract with clients — the two evolve independently on purpose
```

### 17.11 Load Testing

```python
# loadtest/withdrawal_flow.py (Locust)
from locust import HttpUser, task, between

class WithdrawalUser(HttpUser):
    wait_time = between(1, 3)
    @task
    def withdraw(self):
        self.client.post("/api/workflows/withdrawal/start", json={"definition": WITHDRAWAL_DEF, "ctx": sample_ctx()})
```

Run against a staging environment sized to match production shape (replica counts, DB tier), not a laptop — the failure modes you're looking for (connection pool exhaustion, circuit breakers tripping, cache stampedes) only show up under real concurrency.

### 17.12 Canary Deploys, Gated by the Flag Engine You Already Have

```yaml
# .github/workflows/deploy.yml (addition) — reuses §6.6/§13's rules-based flag engine
# instead of introducing a separate feature-flag product
- name: Deploy canary
  run: kubectl set image deployment/api api=myapp:${{ github.sha }} --record
- name: Gate rollout behind a flag
  run: curl -X POST $API/api/flags -d '{"key":"new-adapter-path","rolloutPercent":5}'
- name: Watch error rate, auto-rollback on SLO breach
  run: ./scripts/watch-and-rollback.sh new-adapter-path
```

### 17.13 Disaster Recovery

Mostly process, not code, but non-negotiable process:

- **Postgres**: automated PITR backups (managed RDS/Cloud SQL, or self-managed `pg_basebackup` + WAL archiving).
- **Temporal**: namespace-level workflow history backup (Temporal Cloud handles this; self-hosted needs an explicit export process).
- **Redis**: enable RDB/AOF persistence if it's holding anything beyond a pure ephemeral cache — idempotency keys (§17.2) need to survive a Redis restart.
- **Rehearse the restore.** An untested backup is a hope, not a plan — schedule an actual restore drill, not just backup-job green checkmarks.

### 17.14 SLOs & Error Budgets

Also process, enabled by infrastructure you've already built:

- Define SLOs per critical flow using the trace data from §6.1/§8 — e.g. "99.9% of withdrawals complete end-to-end in under 2 seconds."
- Error budgets gate releases: burning budget too fast pauses non-critical rollouts automatically (tie this into §17.12's canary watcher).
- This can't be calibrated meaningfully until you have real production traffic — reasonable to finalize in month one, not before launch.

---

## 18. References

- OpenTelemetry JS: https://github.com/open-telemetry/opentelemetry-js
- XState: https://github.com/statelyai/xstate
- Temporal TypeScript SDK: https://github.com/temporalio/sdk-typescript
- Redux Toolkit: https://github.com/reduxjs/redux-toolkit
- Redux-Saga: https://github.com/redux-saga/redux-saga
- eslint-plugin-boundaries: https://github.com/javierbrea/eslint-plugin-boundaries
- Lodash (`get`/`set`, used throughout the transform layer): https://github.com/lodash/lodash
- Temporal Python SDK: https://github.com/temporalio/sdk-python
- FastAPI: https://github.com/fastapi/fastapi
- OpenTelemetry Python: https://github.com/open-telemetry/opentelemetry-python
- SQLAlchemy: https://github.com/sqlalchemy/sqlalchemy
- pip-audit: https://github.com/pypa/pip-audit
- Trivy: https://github.com/aquasecurity/trivy
- cryptography (Fernet, used in §16.1): https://github.com/pyca/cryptography
- redis-py (used throughout §17.1/§17.2): https://github.com/redis/redis-py
- Hypothesis (property-based testing, §17.7): https://github.com/HypothesisWorks/hypothesis
- Locust (load testing, §17.11): https://github.com/locustio/locust

*(Package versions and APIs above move fast, especially the OTEL JS surface — check current docs before wiring any of these in for real.)*