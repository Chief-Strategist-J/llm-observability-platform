# Web App Dashboard Implementation Tasks (`packages/node/web-app`)

Prioritized checklist for replacing `<EmptyState />` placeholders with live interactive dashboards.

---

## 🔴 Priority 1: Latency Analytics Dashboard (`/latency`)
- [x] **P1.1**: Connect `latencyClientService.getPercentiles` and `getSLO` to render KPI summary row (P50, P95, P99 Latency, SLO Budget Remaining).
- [x] **P1.2**: Implement **Historical Latency Baseline Table & Percentile Ribbons**.
- [x] **P1.3**: Build **Latency Segment Attribution Breakdown** to display per-segment (DNS, TCP, Queueing, Inference) latency.

---

## 🟠 Priority 2: Quality & Evaluation Dashboard (`/quality`)
- [x] **P2.1**: Connect `qualityClientService.getQualitySummary` to render quality summary stats (Avg Quality Score, Score Delta %, Below SLO Count).
- [x] **P2.2**: Implement **Composite Score & Alert Trend Table** (7-day rolling baseline).
- [x] **P2.3**: Build **Model Quality Distribution Table** showing average, min, max scores by model (`gpt-4o`, `claude-3-5-sonnet`, `gpt-4o-mini`).
- [x] **P2.4**: Add **Flagged Content Panel** displaying toxicity and hallucination alerts.

---

## 🟡 Priority 3: Main Overview Dashboard (`/`)
- [x] **P3.1**: Create **System Summary KPI Row** aggregating Latency P95, Quality Avg Score, Total USD Cost, and Active Spans.
- [x] **P3.2**: Add **System Health & SLO Alert Banner** displaying active burn rate status and error budget health.
- [x] **P3.3**: Embed **Recent Traces Preview Table** showing latest spans with status badges.

---

## 🟢 Priority 4: Trace Explorer (`/traces` & `/traces/[traceId]`)
- [x] **P4.1**: Connect `tracesClientService.listTraces` to build a filterable **Trace Explorer Table**.
- [x] **P4.2**: Implement status indicators (`success` / `error`), model filter, duration, and cost formatting in the trace list.
- [x] **P4.3**: Build **Trace Detail View (`/traces/[traceId]`)** displaying the distributed span execution waterfall graph.

---

## 🔵 Priority 5: Cost Analytics Dashboard (`/costs`)
- [x] **P5.1**: Connect `costsClientService.getCostSummary` to render USD spend summary metrics (Total Spend, Daily Avg, Cost Delta %).
- [x] **P5.2**: Build **Cost Spend Breakdown Table** by provider and model.
- [x] **P5.3**: Add **Run-Rate Monthly Projection** and token consumption metrics.
