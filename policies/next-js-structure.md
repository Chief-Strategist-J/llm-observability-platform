# Complex Logic + Tracing (Generic — extends the previous 3 docs)

From here on, every folder/file uses `<feature>` as a placeholder — nothing below is wallet/auth/dashboard-specific. Swap `<feature>` for `work-order`, `deal`, `automation-definition`, `agent-run`, or whatever entity you're actually modeling.



## 0. How this maps onto the domains you named

| Domain | `<feature>` becomes | Rules complexity | State machine | Workflow steps |
|---|---|---|---|---|
| Work orders | `work-order` | assignment/SLA/escalation, priority-ranked | `open → assigned → in-progress → done/cancelled` | dispatch automation, escalation on SLA breach |
| Sales | `deal` | discount/approval rules composed from tenant + global | `lead → qualified → proposal → negotiation → closed` | quote-to-cash automation |
| Automations (the builder itself) | `automation-definition` | trigger-condition rules | `queued → running → done/failed` | this IS the workflow engine, self-hosted |
| AI workflows | `agent-run` | routing/guardrail rules, often async (safety checks) | `planning → executing → reviewing → done` | multi-step tool calls, human-approval gates |
| Finance | `transaction` | fraud/risk scoring, AML checks (async, sanctions-list lookup), spend-velocity limits, tiered approval thresholds | `pending → authorized → settled/declined → reversed` | fraud-check pipeline (parallel: velocity + sanctions + device check), multi-approver sign-off above threshold, settlement/reconciliation automation |
| Maps | `route` | geofence entry/exit (event-driven, async), service-area eligibility, zone/surge pricing | `planned → en-route → delayed/on-time → arrived/cancelled` | live ETA recalculation on location-update events, nearest-driver dispatch (rank + parallel ping candidates), geofence-triggered notifications |
| Messaging | `conversation` | spam/abuse detection (async, classifier call), routing/priority rules, content moderation | `queued → active → waiting-on-customer/waiting-on-agent → resolved/reopened` | auto-routing to queue/agent, AI-drafted reply + human-approval gate before send, SLA-breach escalation |

Nothing else in this doc names a domain — everything below is the generic engine that produces every one of these.

## 1. Tracing — wired through every layer

This is the centerpiece you asked for. The goal: a single trace shows a user's click, the saga it triggered, which of N business rules fired, every state transition, every workflow step, and the backend spans those steps called into — one waterfall, not five separate log searches.

### 1.1 Tracer setup

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

// auto-injects the traceparent header into every fetch() call — this is what links a frontend
// span to whatever backend span your API creates from the same header, same OTLP pipeline
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

OTLP is the standard here, so this lands in whatever trace backend you're already running on the API side — Tempo, Jaeger, Honeycomb, whatever speaks OTLP — alongside your existing backend spans, in the same trace. *(The OTEL JS API surface moves fast; sanity-check package versions against current docs when you actually wire this in.)*

### 1.2 Traced adapter decorator — same shape as `withRetry`/`withCache`

```typescript
// packages/core/data-driven/adapter-decorators.ts (addition)
import { tracer } from "@core/tracing/tracer";
import type { CrudPort } from "./create-entity-adapter";

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

**Composition order matters:** put `withTracing` outermost — `withTracing(withCircuitBreaker(withCache(withRetry(raw))))` — so the span duration reflects the *full* call including retry backoff and cache-miss latency, not just the final attempt.

### 1.3 Traced rule evaluation — the actual payoff at scale

Aggregated pass/fail is useless when someone asks "why was this denied" and the answer is buried in one of a thousand rules. Every evaluation gets a span listing exactly which rules matched:

```typescript
// packages/core/rules-engine/evaluate.ts (excerpt — full version in §2)
span.setAttribute("rules.total", rules.length);
span.setAttribute("rules.matched_ids", matched.map((r) => r.id).join(","));
span.setAttribute("rules.winning_ids", winners.map((r) => r.id).join(","));
```

Now "why was I denied" is a trace lookup, not a support escalation.

### 1.4 Traced state transitions

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

Every transition becomes a timestamped span event — "why was this stuck in `processing` for 40 seconds" becomes a two-click trace lookup instead of log spelunking.

### 1.5 Traced workflow steps (shown fully in §3.4 — root span per workflow run, child span per step)

### 1.6 Surfacing trace IDs to users/support

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
Support pastes that ID into your trace backend and lands directly on the failing request's full waterfall — frontend click through backend processing — instead of correlating by timestamp.

## 2. Rules engine, deepened for genuinely complex logic

The flat rule list from the earlier doc breaks down once rules can *conflict* or need *live data* to evaluate. Two additions:

```typescript
// packages/core/rules-engine/rule.types.ts — extended
export interface Rule {
  id: string;
  description: string;
  when: RuleCondition;
  effect: string;
  priority?: number;                       // higher wins among matched non-deny rules
  category?: "allow" | "deny" | "modify";   // "deny" always wins, regardless of priority — safety default
}

export type RuleCondition =
  | { op: "eq"; field: string; value: unknown }
  | { op: "in"; field: string; values: unknown[] }
  | { op: "gt" | "lt" | "gte" | "lte"; field: string; value: number }
  | { op: "and"; conditions: RuleCondition[] }
  | { op: "or"; conditions: RuleCondition[] }
  | { op: "not"; condition: RuleCondition }
  | { op: "asyncCheck"; resolver: string };  // real-world rules often need a live fetch, not just context fields
```

```typescript
// packages/core/rules-engine/async-checkers.ts — registry, same Visitor shape as field renderers
type AsyncChecker = (ctx: RuleContext) => Promise<boolean>;
const checkers = new Map<string, AsyncChecker>();
export function registerAsyncChecker(key: string, fn: AsyncChecker) { checkers.set(key, fn); }
export function getAsyncChecker(key: string): AsyncChecker {
  const fn = checkers.get(key);
  if (!fn) throw new Error(`No async checker registered for "${key}"`);
  return fn;
}
```

```typescript
// packages/core/rules-engine/evaluate.ts — async-aware, traced, priority + deny-override resolution
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

```typescript
// packages/core/rules-engine/compose-rules.ts — merge global + tenant + feature rule sets
export function composeRuleSets(...ruleSets: Rule[][]): Rule[] {
  return ruleSets.flat();
}
// usage: composeRuleSets(globalComplianceRules, tenantRules, featureRules)
```

That's four real complexity axes handled as data, not code: **conflicting rules** (deny-overrides, priority-ranked), **live-data-dependent rules** (async, traced), and **layered rule sets** (global/tenant/feature composed at evaluation time).

## 3. Workflow engine — for automations & AI workflows specifically

### 3.1 Step definitions as data

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

### 3.2 Step registry — Visitor pattern again, same shape as field renderers

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

### 3.3 Built-in step types, including branch + parallel for real DAG shape

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
  // live server-side (Temporal or similar). This step calls that endpoint, streams the
  // result back, and traces the round trip. It does NOT reimplement agent orchestration
  // in the browser — see the scope note in §3.5.
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
//   machine (§1.4) driving the approval screen itself
```

### 3.4 Runner — root span per workflow, child span per step

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

### 3.5 Scope boundary — worth stating plainly

This engine composes **what runs and in what order**, renders progress, and traces every step. It is *not* a durable execution engine — no persistence across page reloads, no distributed retries, no exactly-once guarantees. For workflows that must survive a closed tab, a crashed server, or need real retry/backoff semantics at scale (which is most of "millions of complex AI workflow runs"), that execution belongs server-side — a durable orchestrator like Temporal is the standard tool for exactly this. The frontend's `callAI`/`callEntity` steps stay thin clients that kick off and poll/stream that backend execution; this layer's job is the human-facing half — defining the step sequence as data, rendering live progress, and handling approval gates — not re-implementing a workflow engine in the browser.

## 4. Final generic folder structure

```
my-app/
├── apps/web/
│   ├── app/(protected)/<feature>/page.tsx
│   ├── app/{layout.tsx, providers.tsx, middleware.ts}
│   └── e2e/
│
├── packages/
│   ├── core/
│   │   ├── store/{feature-registry.ts, configure-store.ts, root-saga.ts}
│   │   ├── http/http-client.ts                    # fetch-based — auto-traced by FetchInstrumentation
│   │   ├── tracing/tracer.ts                       # OTEL Web SDK + OTLP + fetch auto-instrumentation
│   │   ├── data-driven/
│   │   │   ├── entity-schema.types.ts
│   │   │   ├── create-entity-adapter.ts
│   │   │   ├── create-entity-sagas.ts              # emits eventBus.emit(`${name}.created`, ...) generically
│   │   │   ├── create-entity-slice.ts
│   │   │   ├── adapter-decorators.ts               # withRetry / withCache / withCircuitBreaker / withTracing
│   │   │   └── register-entity.ts
│   │   ├── rules-engine/
│   │   │   ├── rule.types.ts
│   │   │   ├── async-checkers.ts
│   │   │   ├── evaluate.ts                         # priority + deny-override + async, traced
│   │   │   └── compose-rules.ts
│   │   ├── state-machines/use-data-machine.ts       # traced transitions
│   │   ├── workflow-engine/
│   │   │   ├── step.types.ts
│   │   │   ├── step-registry.ts
│   │   │   ├── builtin-steps.ts                     # evaluateRules / callEntity / callAI / branch / parallel / humanApproval
│   │   │   └── run-workflow.ts                      # traced root span + per-step child spans
│   │   ├── feature-flags/resolve-flag.ts
│   │   ├── event-bus/event-bus.ts
│   │   └── testing/{test-store.ts, msw-handlers/}
│   │
│   ├── shared/
│   │   ├── ui/{DataForm.tsx, DataTable.tsx, field-renderers/}
│   │   └── lib/current-trace-id.ts
│   │
│   ├── features/
│   │   └── <feature>/
│   │       ├── schema/<feature>.schema.ts
│   │       ├── rules/<feature>.rules.ts             # priority, category, async conditions as needed
│   │       ├── machines/<feature>.machine.ts
│   │       ├── workflows/<feature>-automation.workflow.ts
│   │       ├── overrides/                           # hand-written — only genuinely non-generic logic
│   │       ├── readModels/
│   │       ├── ui/{*.stories.tsx, *Flow.tsx}
│   │       ├── tests/
│   │       └── index.ts
│   │
│   └── config/{eslint-boundaries.config.js, env.schema.ts}
│
├── .github/workflows/{ci.yml, deploy.yml}
├── turbo.json
└── package.json
```

## 5. One `<feature>` wired end to end

```typescript
// packages/features/<feature>/index.ts
import { createEntityAdapter } from "@core/data-driven/create-entity-adapter";
import { withTracing, withCircuitBreaker, withCache, withRetry } from "@core/data-driven/adapter-decorators";
import { registerEntity } from "@core/data-driven/register-entity";
import { featureSchema } from "./schema/<feature>.schema";
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

Fifteen lines: fully-wired CRUD, resilient (retry + cache + circuit breaker), traced end-to-end into your existing trace backend, rule-aware, and workflow-capable. Everything upstream of this file (adapter factory, saga factory, tracing decorator, rule engine, workflow runner) is written exactly once in `core/` and shared by every `<feature>` you add.

===========
==========================================
===========
# Extreme-Scale Frontend — Complete Structure + Design Pattern Catalog

*(Extends `nextjs-frontend-architecture.md` and `nextjs-data-driven-layer.md`. Those two still hold for the base CRUD-generation code — adapter/saga/slice factories, DataForm/DataTable, Storybook/MSW wiring. This doc closes the gaps: branching logic wasn't data-driven, cross-cutting code (retry/cache/logging) was still repeated per adapter, and field rendering was a stub.)*

## 0. What was still hardcoded, and what closes it

| Gap | Fix | Section |
|---|---|---|
| Business rules (tier/region/KYC/fees) as `if/else` | **Rules Engine** — rules are data, evaluated generically | §3 |
| Multi-step flows as nested `useState`/conditionals | **State Machines** — flows are data (states + transitions) | §4 |
| Retry/cache/logging copy-pasted per adapter | **Decorator composition** — written once, applied by wrapping | §5 |
| `FieldRenderer` stub / central switch statement | **Visitor registry** — field kinds self-register | §6 |
| Cross-feature side effects requiring imports | **Event Bus** — publish/subscribe, zero coupling | §7 |
| Feature flags as ad hoc conditionals | Flags as a **named rule** with rollout %, same engine as §3 | §8 |
| Massive read volume re-deriving the same data | **CQRS-lite read models** — memoized selectors separate from write-side | §9 |


## 10. Complete design pattern catalog

| Pattern | Category | Lives in | Problem it solves |
|---|---|---|---|
| Port & Adapter (Hexagonal) | Structural | `ports/`, `adapters/` | swap infra without touching business logic |
| Anti-corruption layer | Structural | adapter's zod `.parse()` | backend contract drift stops at the seam |
| Decorator | Structural | `adapter-decorators.ts` | retry/cache/circuit-breaking written once, applied everywhere |
| Facade | Structural | `core/http/http-client.ts` | one client surface hides fetch/axios/tracing details |
| Proxy | Structural | `withCache` decorator | transparent request caching/dedup |
| Factory | Creational | `create-entity-*.ts` | generate adapter/saga/slice from schema |
| Builder | Creational | rule/machine composition | fluent construction of complex rule sets |
| Dependency Injection | Creational | `registerEntity()`, saga factories | swappable, mockable wiring, no hardcoded `new` |
| Strategy | Behavioral | rule `effect` consumed as branching strategy | swap behavior by data, not by editing code |
| Specification | Behavioral | `RuleCondition` and/or/not composition | compose business rules declaratively |
| Chain of Responsibility | Behavioral | saga/rule pipeline ordering | ordered checks: auth → rate-limit → validate → execute |
| State Machine | Behavioral | `machines/*.machine.ts` | explicit states/transitions instead of nested conditionals |
| Visitor | Behavioral | `field-renderers/registry.ts` | extensible rendering, no central switch statement |
| Observer / Pub-Sub | Behavioral | `event-bus` | cross-feature effects without cross-feature imports |
| Command | Behavioral | dispatched actions | serializable actions enable offline queue, undo, audit log |
| CQRS | Architectural | `state/` (write) vs `readModels/` (read) | reads don't contend with or duplicate write-side logic |
| Saga (orchestration) | Architectural | generated + `overrides/` sagas | coordinate async workflows, retries, cancellation |
| Feature Flags / Progressive Delivery | Architectural | `core/feature-flags` | ship many variants without a new code path per variant |
| Micro-frontends / Module Federation | Org-scale | separate `apps/` per team, if/when needed | independent deploy cadence across many teams |
| Circuit Breaker + Bulkhead | Resilience | `http-client` / adapter decorators | one flaky dependency doesn't cascade-fail the app |
| Edge / ISR / PPR rendering | Infra-scale | Next.js route segment config | serve massive concurrent read traffic from cache/edge |

## 11. Two different kinds of "scale," worth naming separately

Everything above keeps the **codebase** scalable — hundreds of features, many engineers, low coupling, fast CI, minimal repetition. That's what design patterns actually govern.

Serving genuinely massive **traffic** (millions of concurrent requests) is overwhelmingly a CDN/edge/backend/database problem — sharding, load balancing, edge caching. The frontend's job there is narrower but concrete: be stateless per-request, cacheable, and edge-renderable. Concretely, in this stack that means leaning on Next.js's route-segment `revalidate`/ISR, streaming SSR, and keeping client bundles small via the per-feature code-splitting from doc 1 — so the origin does as little work as possible per request. Worth keeping the two separate so you're solving traffic-scale problems in the infra layer and codebase-scale problems in the patterns above, rather than expecting one to fix the other.