import time
import threading
from typing import Dict, Optional
from python_shared.http.constants import HTTP_CONSTANTS

class CircuitState:
    def __init__(self, state: str = HTTP_CONSTANTS.CIRCUIT_CLOSED, failures: int = 0):
        self.state = state
        self.failures = failures
        self.last_failure_time: Optional[float] = None
        self.next_attempt_time: Optional[float] = None

class StandardCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_ms: float = 3600000.0,
        max_entries: int = 1000
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_ms = cooldown_ms
        self.max_entries = max_entries
        self._states: Dict[str, CircuitState] = {}
        self._lock = threading.RLock()

    def get_circuit_key(self, tenant_id: str, route_template_or_url: str) -> str:
        return f"{tenant_id}:{route_template_or_url}"

    def can_execute(self, circuit_key: str) -> bool:
        with self._lock:
            state = self._states.get(circuit_key)
            if not state or state.state == HTTP_CONSTANTS.CIRCUIT_CLOSED:
                return True

            now = time.time() * 1000.0
            if state.state == HTTP_CONSTANTS.CIRCUIT_OPEN:
                if state.next_attempt_time and now >= state.next_attempt_time:
                    state.state = HTTP_CONSTANTS.CIRCUIT_HALF_OPEN
                    return True
                return False

            if state.state == HTTP_CONSTANTS.CIRCUIT_HALF_OPEN:
                return True

            return True

    def on_success(self, circuit_key: str) -> None:
        with self._lock:
            state = self._states.get(circuit_key)
            if state:
                state.state = HTTP_CONSTANTS.CIRCUIT_CLOSED
                state.failures = 0
                state.next_attempt_time = None

    def on_failure(self, circuit_key: str) -> None:
        now = time.time() * 1000.0
        with self._lock:
            state = self._states.get(circuit_key)
            if not state:
                self._evict_if_full()
                state = CircuitState(state=HTTP_CONSTANTS.CIRCUIT_CLOSED, failures=0)
                self._states[circuit_key] = state

            state.failures += 1
            state.last_failure_time = now

            if state.failures >= self.failure_threshold or state.state == HTTP_CONSTANTS.CIRCUIT_HALF_OPEN:
                state.state = HTTP_CONSTANTS.CIRCUIT_OPEN
                state.next_attempt_time = now + self.cooldown_ms

    def get_state(self, circuit_key: str) -> Optional[CircuitState]:
        with self._lock:
            return self._states.get(circuit_key)

    def _evict_if_full(self) -> None:
        if len(self._states) >= self.max_entries:
            oldest_key = next(iter(self._states.keys()), None)
            if oldest_key:
                del self._states[oldest_key]
