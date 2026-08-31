# Web App Dashboard Implementation Tasks (`packages/node/web-app`)

Prioritized checklist for replacing `<EmptyState />` placeholders with live interactive dashboards.

---

## 🔴 Priority 1: Latency Analytics Dashboard (`/latency`)
- [ ] **P1.1**: Connect `trpc.latency.getSummary` to render `MetricCard` summary row (Average TTFT, P95 Latency, P99 Latency, SLO Breach Count).
- [ ] **P1.2**: Implement **Percentile Trend Chart** (P50, P95, P99 time-series) using `trpc.latency.getPercentiles`.
- [ ] **P1.3**: Build **Model & Endpoint Breakdown Table** using `DataTable` to display per-endpoint latency metrics and `SeverityBadge` indicators.

---

## 🟠 Priority 2: Quality & Evaluation Dashboard (`/quality`)
- [x] **P2.1**: Connect `qualityClientService.getQualitySummary` to render quality summary stats (Avg Quality Score, Score Delta %, Below SLO Count).
- [x] **P2.2**: Implement **Composite Score & Alert Trend Table** (7-day rolling baseline).
- [x] **P2.3**: Build **Model Quality Distribution Table** showing average, min, max scores by model (`gpt-4o`, `claude-3-5-sonnet`, `gpt-4o-mini`).
- [x] **P2.4**: Add **Flagged Content Panel** displaying toxicity and hallucination alerts.

---

## 🟡 Priority 3: Main Overview Dashboard (`/`)
- [ ] **P3.1**: Create **System Summary KPI Row** aggregating Latency P95, Quality Avg Score, Total USD Cost, and Total Spans.
- [ ] **P3.2**: Add **System Health & SLO Alert Banner** displaying active burn rate alerts (`page`, `slack`, `ticket`).
- [ ] **P3.3**: Embed **Recent Traces Preview Table** showing top 5 latest spans with status badges.

---

## 🟢 Priority 4: Trace Explorer (`/traces` & `/traces/[traceId]`)
- [ ] **P4.1**: Connect `trpc.trace.list` to build a filterable, paginated **Trace Explorer Table**.
- [ ] **P4.2**: Implement status indicators (`success` / `error`), model filter, and duration formatting in the trace list.
- [ ] **P4.3**: Build **Trace Detail View (`/traces/[traceId]`)** displaying the distributed span execution waterfall graph.

---

## 🔵 Priority 5: Cost Analytics Dashboard (`/costs`)
- [ ] **P5.1**: Connect `trpc.cost.getSummary` to render USD spend summary metrics (Total Cost, Daily Avg, Cost Delta %).
- [ ] **P5.2**: Build **Cost Spend Breakdown Chart** by provider and model.
- [ ] **P5.3**: Add **Token Consumption Breakdown Table** (Input vs Output tokens per provider).
