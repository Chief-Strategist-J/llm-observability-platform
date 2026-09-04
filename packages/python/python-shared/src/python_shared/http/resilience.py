import time
import logging
from typing import Callable, Any, TypeVar

T = TypeVar("T")
logger = logging.getLogger("python_shared.http.resilience")

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_state_change = time.time()

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout:
                self.state = "HALF-OPEN"
                self.last_state_change = now
                logger.info("CircuitBreaker transitioning to HALF-OPEN")
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN. Request blocked.")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("CircuitBreaker recovered to CLOSED")
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_state_change = time.time()
                logger.error(f"CircuitBreaker tripped to OPEN after {self.failure_count} failures")
            raise e
