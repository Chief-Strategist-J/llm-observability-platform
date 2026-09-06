from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class LatencyQuerySelector:
    model: str
    hour_of_day: int
    quantile: float = 0.99


class QuerySelectors:
    @staticmethod
    def select_model_hour_key(model: str, hour_of_day: int) -> str:
        return f"sketch:total:{model}:{hour_of_day}"

    @staticmethod
    def select_slo_key(model: str, endpoint: str, bucket: int) -> str:
        return f"slo:total:{model}:{endpoint}:{bucket}"
