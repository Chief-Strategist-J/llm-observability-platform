# Frontend Knowledge Base (Starter)

## Recommended stack
- React + TypeScript + Vite
- TanStack Query for polling backend endpoints
- Zustand for local UI state
- Recharts for summary charts
- D3 for waterfall + dependency graph rendering

## Backend integration notes
- Backend is request/response only (no WebSocket stream).
- Use polling with `refetchInterval` for:
  - `/health` every 10s
  - `/api/v1/analysis/results` every 3-5s for trace table
- Trigger processing using `POST /api/v1/flush` and refresh queries on success.

## Minimal page plan
1. **Home (`/`)**
   - HealthStatusBar
   - FlushTriggerPanel
   - TraceListTable
2. **Trace Detail (`/traces/:id`)**
   - TraceWaterfallView (placeholder first)
   - CriticalPathOverlay (once waterfall spans are rendered)
   - AnomalyScorePanel
3. **Clusters (`/clusters`)**
   - ClusterDistributionChart
   - LatencyHistogram

## Data model assumptions
- `AnalysisResult` has:
  - `trace_id`
  - `cluster_id`
  - `critical_path`
  - anomaly fields/scores
- Use paginated endpoint with `limit` and `offset`.

## Implementation status
- Initial Vite frontend scaffold is added in `web/` with:
  - API client wrapper
  - Query provider
  - Health status polling
  - Flush trigger panel
  - Basic trace list table rendering
