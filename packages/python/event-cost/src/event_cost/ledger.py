from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

from event_cost.backends._base import Backend
from event_cost.backends.sqlite import SQLiteBackend

@dataclass
class SpanInput:
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    org_id: str = ""
    project_id: str = ""
    service_name: str = ""
    user_id: str = ""
    estimated_tokens: int = 0
    cost_usd_micro: int | None = None

def _load_prices(price_config_path: str | None = None) -> dict[tuple[str, str], dict]:
    if price_config_path is None:
        price_config_path = str(Path(__file__).parent / "prices" / "builtin.yaml")
    prices = {}
    try:
        with open(price_config_path) as f:
            data = yaml.safe_load(f) or {}
        for entry in data.get("prices", []):
            model = entry["model"]
            provider = entry["provider"]
            prices[(model, provider)] = entry
    except FileNotFoundError:
        pass
    return prices

def _compute_cost(span: SpanInput, prices: dict[tuple[str, str], dict]) -> int:
    key = (span.model, span.provider)
    if key in prices:
        entry = prices[key]
        return (
            span.prompt_tokens * entry["input_price_per_token_micro"]
            + span.completion_tokens * entry["output_price_per_token_micro"]
        )
    return 0

class CostLedger:
    def __init__(
        self,
        backend: Backend | None = None,
        price_config_path: str | None = None,
    ) -> None:
        self._backend = backend or SQLiteBackend()
        self._prices = _load_prices(price_config_path)

    def record(self, **kwargs) -> None:
        span = SpanInput(**kwargs)
        cost = span.cost_usd_micro
        if cost is None:
            cost = _compute_cost(span, self._prices)
        self._backend.record(span, cost)

    def total_cost_usd(
        self,
        org_id: str,
        window: str = "24h",
        project_id: str | None = None,
        service_name: str | None = None,
        model: str | None = None,
    ) -> float:
        micro = self._backend.query_total(
            org_id=org_id,
            window=window,
            project_id=project_id,
            service_name=service_name,
            model=model,
        )
        return micro / 1000000

    def budget_remaining(self, org_id: str, project_id: str = "") -> float:
        return self._backend.get_budget(org_id, project_id) / 1000000

    def set_budget(self, org_id: str, budget_usd: float, project_id: str = "") -> None:
        self._backend.set_budget(org_id, project_id, int(budget_usd * 1000000))

    def is_anomaly(self, service_name: str, model: str) -> bool:
        return self._backend.check_anomaly(service_name, model)
