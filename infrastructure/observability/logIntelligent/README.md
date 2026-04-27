# logIntelligent

Feature-based log intelligence module following ports-and-adapters with a single composition root.

## Purpose

- Ingest raw logs and generate stable templates.
- Enrich logs structurally and semantically.
- Score anomalies and maintain frequency/drift intelligence.
- Support trace lookup and semantic similarity search.
- Route records by hot/warm/cold tier policy.

## Structure

```text
logIntelligent/
├── api/
├── client/
├── domain/
├── ingestion/
├── enrichment/
├── intelligence/
├── storage/
├── test/
├── CONNASCENCE.md
├── dependencies.py
├── models.py
└── pipeline.py
```

## Runtime flow

1. `LogIntelligencePipeline.ingest` parses a message into `template_id`.
2. Structural enrichment extracts and normalizes fields.
3. Frequency + drift + anomaly scoring run in sequence.
4. Embedding cache generates/reuses vector and updates semantic index.
5. Trace index updates from `trace_id`.
6. Storage router decides `hot`/`warm`/`cold` tier.

## Run API locally

```bash
python -m infrastructure.observability.logIntelligent.api.run
```

Default address: `http://localhost:8113`

## API endpoints

- `GET /health`
- `GET /api/v1/log-intelligence/metrics/capability`
- `POST /api/v1/log-intelligence/ingest`
- `POST /api/v1/log-intelligence/ingest/batch`
- `GET /api/v1/log-intelligence/logs/{line_id}`
- `GET /api/v1/log-intelligence/templates/{template_id}/similar?k=5`
- `GET /api/v1/log-intelligence/traces/{trace_id}`

## Quick curl usage

```bash
curl -s http://localhost:8113/health

curl -s http://localhost:8113/api/v1/log-intelligence/metrics/capability

curl -s -X POST http://localhost:8113/api/v1/log-intelligence/ingest \
  -H 'Content-Type: application/json' \
  -d '{"line_id":"l1","message":"2026-04-27T10:00:00Z ERROR service=auth trace_id=t1 login failed for user 101"}'

curl -s -X POST http://localhost:8113/api/v1/log-intelligence/ingest/batch \
  -H 'Content-Type: application/json' \
  -d '{"logs":[{"line_id":"l2","message":"2026-04-27T10:00:01Z WARN service=auth trace_id=t1 retry user 101"}]}'
```

## Python client usage

```python
from infrastructure.observability.logIntelligent.client.api_client import LogIntelligenceApiClient

client = LogIntelligenceApiClient("http://localhost:8113")
print(client.health())
print(client.capability_metrics())
item = client.ingest("l3", "2026-04-27T10:00:02Z INFO service=auth trace_id=t1 ok user 101")
print(item)
print(client.log_lookup("l3"))
print(client.trace_lookup("t1"))
print(client.similar_templates(item["template_id"], k=3))
```

## Capability metrics definition

`GET /api/v1/log-intelligence/metrics/capability` returns:

- `implemented`: features fully delivered.
- `partial`: features delivered with fallback/placeholder or limited scope.
- `pending`: features not yet delivered.
- `readiness_score`: weighted progress ratio `(implemented + 0.5 * partial) / total`.

## Testing

Run module tests only:

```bash
python -m unittest infrastructure/observability/logIntelligent/test/test_log_intelligent_arch.py
```

Run observability-scope tests:

```bash
python -m unittest discover infrastructure/observability
```
