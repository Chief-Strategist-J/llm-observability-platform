from prometheus_client import Counter
from budget_provisioner.shared.ports.metrics_port import MetricsPort

REQUESTS = Counter(
    "budget_provisioner_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status_code"]
)

INVALIDATIONS = Counter(
    "budget_cache_invalidations_total",
    "Total budget cache invalidations triggered",
    ["user_id", "model"]
)

class PrometheusAdapter(MetricsPort):
    def __init__(self) -> None:
        self._requests = REQUESTS
        self._invalidations = INVALIDATIONS

    def record_request(self, method: str, path: str, status_code: int) -> None:
        self._requests.labels(method=method, path=path, status_code=status_code).inc()

    def record_invalidation(self, user_id: str, model: str) -> None:
        self._invalidations.labels(user_id=user_id, model=model).inc()
