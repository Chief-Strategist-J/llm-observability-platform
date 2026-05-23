import threading
from typing import Dict, List, Tuple, Any

class FallbackTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._trace_models: Dict[str, List[str]] = {}
        self._trace_attempts: Dict[str, int] = {}

    def track(self, trace_id: str, model: str) -> Tuple[int, List[str]]:
        if not trace_id:
            return 0, [model] if model else []
        trace_id_str = str(trace_id)
        with self._lock:
            if trace_id_str not in self._trace_models:
                self._trace_models[trace_id_str] = []
                self._trace_attempts[trace_id_str] = 0
            else:
                self._trace_attempts[trace_id_str] += 1

            if model:
                self._trace_models[trace_id_str].append(model)

            return self._trace_attempts[trace_id_str], list(self._trace_models[trace_id_str])

    def clear(self) -> None:
        with self._lock:
            self._trace_models.clear()
            self._trace_attempts.clear()

_TRACKER = FallbackTracker()

def track_fallback(trace_id: Any, model: str) -> Tuple[int, List[str]]:
    return _TRACKER.track(trace_id, model)

def clear_fallback_tracker() -> None:
    _TRACKER.clear()
