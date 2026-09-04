from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"]
)

ACTIVE_WORKERS = Gauge(
    "active_workers_total",
    "Total active worker threads or tasks",
    ["worker_type"]
)
