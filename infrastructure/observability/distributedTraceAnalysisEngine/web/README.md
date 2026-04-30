# Trace Analysis Web (Starter)

## Local run
```bash
cd infrastructure/observability/distributedTraceAnalysisEngine/web
npm install
npm run dev
```

UI URL: `http://localhost:5173`

Optional env var:
- `VITE_TRACE_API_BASE` (default `http://localhost:8090`)

## Docker run (recommended)
From `infrastructure/observability/distributedTraceAnalysisEngine`:
```bash
docker compose up --build dtae-server dtae-web
```

- API: `http://localhost:8090`
- UI: `http://localhost:5173`

## Included
- Health status bar (`/health` polling)
- Flush trigger panel (`POST /api/v1/flush`)
- Trace list table (`GET /api/v1/analysis/results?limit=&offset=`)
- Trace detail area:
  - Waterfall view
  - Critical path overlay summary
  - Service dependency graph summary
  - Anomaly score panel
- Overview area:
  - Cluster distribution
  - Latency histogram
