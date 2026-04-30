# Analysis Results Pagination & Filtering

## Endpoint
`GET /api/v1/analysis/results`

## Query parameters
- `limit` (optional, integer): number of results to return.
  - default: `100`
  - max: `1000`
- `offset` (optional, integer): number of records to skip.
  - default: `0`
- `trace_id` (optional, string): filter results to a specific trace id.

## Behavior
1. If `trace_id` is provided, results are filtered to matching trace IDs.
2. `offset` is applied to filtered results.
3. `limit` is applied after offset.

## Examples
- First page:
  - `/api/v1/analysis/results?limit=50&offset=0`
- Next page:
  - `/api/v1/analysis/results?limit=50&offset=50`
- Single trace lookup via list endpoint:
  - `/api/v1/analysis/results?trace_id=4bf92f3577b34da6a3ce929d0e0e4736`
