import threading

class ConcurrencyAdmissionControl:
    def __init__(self, max_capacity: int = 500):
        self.max_capacity = max_capacity
        self.active_in_flight = 0
        self._lock = threading.RLock()

    def acquire(self) -> bool:
        with self._lock:
            if self.active_in_flight >= self.max_capacity:
                return False
            self.active_in_flight += 1
            return True

    def release(self) -> None:
        with self._lock:
            if self.active_in_flight > 0:
                self.active_in_flight -= 1

    def get_active_count(self) -> int:
        with self._lock:
            return self.active_in_flight

    def get_max_capacity(self) -> int:
        return self.max_capacity
