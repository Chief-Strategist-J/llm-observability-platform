from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple


class MetricType(str, Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    metric_type: MetricType
    description: str
    unit: str


@dataclass(frozen=True)
class MetricEvaluator:
    metric: MetricDefinition
    extract_fn: Callable[[Dict[str, Any]], Optional[Tuple[Any, Dict[str, str]]]]


def _service_labels(span: Dict[str, Any]) -> Dict[str, str]:
    return {"service_name": str(span.get("service_name", "unknown"))}


def _base_labels(span: Dict[str, Any]) -> Dict[str, str]:
    return {
        "model": str(span.get("model", "unknown")),
        "provider": str(span.get("provider", "unknown")),
        "service_name": str(span.get("service_name", "unknown")),
    }


def _extract_toxicity_detected(
    span: Dict[str, Any],
) -> Optional[Tuple[int, Dict[str, str]]]:
    score = span.get("toxicity_score")
    flag = span.get("toxicity_detected")
    if flag or (score is not None and float(score) > 0.50):
        return 1, _service_labels(span)
    return None


def _extract_toxicity_score(
    span: Dict[str, Any],
) -> Optional[Tuple[float, Dict[str, str]]]:
    score = span.get("toxicity_score")
    if score is None:
        return None
    return float(score), _base_labels(span)


SAFETY_METRICS_REGISTRY: Tuple[MetricEvaluator, ...] = (
    MetricEvaluator(
        metric=MetricDefinition(
            name="llm_toxicity_detected_total",
            metric_type=MetricType.COUNTER,
            description="Total toxicity detections above threshold",
            unit="1",
        ),
        extract_fn=_extract_toxicity_detected,
    ),
    MetricEvaluator(
        metric=MetricDefinition(
            name="llm_toxicity_score",
            metric_type=MetricType.HISTOGRAM,
            description="Distribution of raw toxicity scores per span",
            unit="1",
        ),
        extract_fn=_extract_toxicity_score,
    ),
)
