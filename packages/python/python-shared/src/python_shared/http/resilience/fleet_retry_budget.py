from typing import Dict, Any

class FleetRetryBudget:
    def __init__(self, max_retry_ratio: float = 0.2, min_requests_threshold: int = 10):
        self.max_retry_ratio = max_retry_ratio
        self.min_requests_threshold = min_requests_threshold
        self.total_requests = 0
        self.total_retries = 0

    def record_request(self) -> None:
        self.total_requests += 1

    def record_retry(self) -> None:
        self.total_retries += 1

    def can_retry(self) -> bool:
        if self.total_requests < self.min_requests_threshold:
            return True
        ratio = self.total_retries / self.total_requests
        return ratio <= self.max_retry_ratio

    def get_stats(self) -> Dict[str, Any]:
        ratio = self.total_retries / self.total_requests if self.total_requests > 0 else 0.0
        return {
            "totalRequests": self.total_requests,
            "totalRetries": self.total_retries,
            "ratio": ratio,
        }
