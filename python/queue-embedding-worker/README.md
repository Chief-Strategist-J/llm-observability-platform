# Queue Embedding Worker

## Decision Tree (ASCII)

```text
Client / Queue Event
        |
        v
+-----------------------+
| api.execute(...)      |  (or direct worker.handle_job)
+-----------------------+
        |
        | opens span: "api.execute"
        v
+-----------------------+
| worker.handle_job     |
+-----------------------+
        |
        | load_config(env)
        |  - dimensions
        |  - embedding_provider
        |
        | opens span: "queue.consume"
        v
+-----------------------+
| JOB_REGISTRY lookup   |
+-----------------------+
        |
        | if job missing -> KeyError("Unknown job ...")
        v
+-------------------------------+
| registry built at import-time |
+-------------------------------+
        |
        | load + validate contract
        | validate handler signature
        v
+-----------------------+
| job.handler(...)      |
| enrich_span(...)      |
+-----------------------+
        |
        | validate payload/dataclass
        | validate dimensions > 0
        | validate text non-empty
        v
+-------------------------------+
| resolve_embedding_provider()  |
+-------------------------------+
   |            |             |
 cloudflare    openai        mock
   |            |             |
   +------------+-------------+
                |
                v
+-------------------------------------------+
| provider.create_embedding(request, dims)  |
+-------------------------------------------+
                |
                v
+-------------------------------------------+
| return normalized result                  |
+-------------------------------------------+
```

## API examples

### Health

```bash
curl -s http://localhost:8080/health
```

Example response:

```json
{
  "status": "ok",
  "queue": "span-enrichment",
  "concurrency": 5,
  "rate_limit_per_sec": 50
}
```

### Execute enrich-span

```bash
curl -s -X POST http://localhost:8080/execute/enrich-span \
  -H 'content-type: application/json' \
  -d '{
    "trace_id": "trace-1",
    "span_id": "span-1",
    "model": "text-embedding-3-small",
    "text": "payment failed for order #123"
  }'
```

Example response:

```json
{
  "status": "processed",
  "job": "enrich-span",
  "result": {
    "trace_id": "trace-1",
    "span_id": "span-1",
    "embedding_key": "emb_1234567890abcdef123456",
    "dimensions": 1536,
    "model": "text-embedding-3-small",
    "provider": "cloudflare"
  }
}
```
