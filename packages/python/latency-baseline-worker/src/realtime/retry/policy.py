from realtime.retry.types import RetryConfig
from realtime.retry.backoff import Backoff

class RetryPolicy:
    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()
        self.attempts = 0

    def next_delay(self) -> float | None:
        """Get the next retry delay. Returns None if max attempts exceeded."""
        self.attempts += 1
        if self.attempts >= self.config.max_attempts:
            return None
        return Backoff.calculate_delay(self.attempts, self.config)

    def reset(self) -> None:
        """Reset the attempt counter on successful connection."""
        self.attempts = 0
