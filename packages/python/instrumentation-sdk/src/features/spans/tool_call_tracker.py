import threading
from typing import Dict, List, Tuple, Any

class ToolCallTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._trace_costs: Dict[str, int] = {}
        self._trace_spans: Dict[str, List[str]] = {}

    def track(self, trace_id: str, span_id: str, cost: int) -> int:
        if not trace_id:
            return cost
        trace_id_str = str(trace_id)
        span_id_str = str(span_id) if span_id else ""
        with self._lock:
            if trace_id_str not in self._trace_spans:
                self._trace_spans[trace_id_str] = []
            if span_id_str and span_id_str not in self._trace_spans[trace_id_str]:
                self._trace_spans[trace_id_str].append(span_id_str)
                if trace_id_str not in self._trace_costs:
                    self._trace_costs[trace_id_str] = 0
                self._trace_costs[trace_id_str] += cost
            return self._trace_costs.get(trace_id_str, cost)

    def get_total_cost(self, trace_id: str) -> int:
        if not trace_id:
            return 0
        trace_id_str = str(trace_id)
        with self._lock:
            return self._trace_costs.get(trace_id_str, 0)

    def clear(self) -> None:
        with self._lock:
            self._trace_costs.clear()
            self._trace_spans.clear()

_TRACKER = ToolCallTracker()

def track_tool_call(trace_id: Any, span_id: Any, cost: int) -> int:
    return _TRACKER.track(trace_id, span_id, cost)

def get_trace_total_cost(trace_id: Any) -> int:
    return _TRACKER.get_total_cost(trace_id)

def clear_tool_call_tracker() -> None:
    _TRACKER.clear()
