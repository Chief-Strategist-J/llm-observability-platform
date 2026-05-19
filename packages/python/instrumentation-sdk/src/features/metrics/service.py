import os
from typing import Any, Dict, List, Optional
import yaml
from .ports import MetricsPort


class MetricsService:
    def __init__(self, adapter: MetricsPort, prices: Optional[List[Dict[str, Any]]] = None):
        self._adapter = adapter
        self._prices = prices or self._load_prices()

    def _load_prices(self) -> List[Dict[str, Any]]:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "config",
            "model_prices.yaml",
        )
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or []
        except Exception:
            return []

    def _find_price(self, model: str, provider: str) -> Optional[Dict[str, Any]]:
        for entry in self._prices:
            if entry.get("model") == model and entry.get("provider") == provider:
                return entry
        for entry in self._prices:
            if entry.get("model") == model:
                return entry
        return None

    def _compute_cost(self, span_data: Dict[str, Any]) -> None:
        if span_data.get("cost_usd_micro") is not None and span_data["cost_usd_micro"] > 0:
            return

        model = span_data.get("model", "")
        provider = span_data.get("provider", "")
        price = self._find_price(model, provider)
        if price is None:
            return

        input_tokens = span_data.get("prompt_tokens", 0) or 0
        output_tokens = span_data.get("completion_tokens", 0) or 0
        input_price = float(price.get("input_price_per_1m", 0))
        output_price = float(price.get("output_price_per_1m", 0))
        cost_usd = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
        cost_micro = int(cost_usd * 1_000_000)
        span_data["cost_usd_micro"] = cost_micro
        span_data["price_version"] = price.get("version", "unknown")

    def record_span_telemetry(self, span_data: Dict[str, Any]) -> None:
        try:
            self._record(span_data)
        except Exception:
            pass

    def _record(self, span_data: Dict[str, Any]) -> None:
        self._compute_cost(span_data)

        model = str(span_data.get("model", "unknown"))
        provider = str(span_data.get("provider", "unknown"))
        service_name = str(span_data.get("service_name", "unknown"))
        status = str(span_data.get("status", "unknown"))
        base_labels = {"model": model, "provider": provider, "service_name": service_name}

        prompt_tokens = span_data.get("prompt_tokens", 0) or 0
        completion_tokens = span_data.get("completion_tokens", 0) or 0
        if prompt_tokens > 0:
            self._adapter.record_tokens(
                prompt_tokens, {**base_labels, "token_type": "prompt"}
            )
        if completion_tokens > 0:
            self._adapter.record_tokens(
                completion_tokens, {**base_labels, "token_type": "completion"}
            )

        cost = span_data.get("cost_usd_micro", 0) or 0
        if cost > 0:
            self._adapter.record_cost(cost, base_labels)

        latency = span_data.get("latency_ms_total", 0) or 0
        if latency > 0:
            self._adapter.record_latency(latency, base_labels)

        ttft = span_data.get("latency_ms_ttft", 0) or 0
        if ttft > 0:
            self._adapter.record_ttft(ttft, base_labels)

        if span_data.get("pii_detected"):
            self._adapter.record_pii({"service_name": service_name})

        if span_data.get("injection_attempt"):
            self._adapter.record_injection({"service_name": service_name})

        finish_reason = span_data.get("finish_reason")
        if finish_reason is not None:
            self._adapter.record_finish_reason(
                {"finish_reason": str(finish_reason), **base_labels}
            )

        has_retries = "true" if span_data.get("retry_count", 0) else "false"
        self._adapter.record_span(
            {**base_labels, "status": status, "has_retries": has_retries}
        )
