from __future__ import annotations

from typing import Any, Dict, List

import requests


class LogIntelligenceApiClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def capability_metrics(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/v1/log-intelligence/metrics/capability", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def ingest(self, line_id: str, message: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/log-intelligence/ingest",
            json={"line_id": line_id, "message": message},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def ingest_batch(self, logs: List[Dict[str, str]]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/log-intelligence/ingest/batch",
            json={"logs": logs},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def similar_templates(self, template_id: str, k: int = 5) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/log-intelligence/templates/{template_id}/similar",
            params={"k": k},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def trace_lookup(self, trace_id: str) -> List[str]:
        response = requests.get(
            f"{self.base_url}/api/v1/log-intelligence/traces/{trace_id}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["line_ids"]

    def log_lookup(self, line_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/log-intelligence/logs/{line_id}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
