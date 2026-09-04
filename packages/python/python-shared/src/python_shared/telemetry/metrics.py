from prometheus_client import Counter, Histogram, Gauge, REGISTRY

# Common metrics templates
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

ACTIVE_WORKERS = Gauge(
    "active_workers_count",
    "Number of active background worker tasks",
    ["worker_name"]
)
