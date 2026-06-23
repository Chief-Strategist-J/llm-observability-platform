import random
from realtime.retry.types import RetryConfig

class Backoff:
    @staticmethod
    def calculate_delay(attempt: int, config: RetryConfig) -> float:
        """Calculate delay using exponential backoff with jitter."""
        if attempt <= 0:
            return 0.0
        
        delay = config.initial_delay * (config.backoff_factor ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            # Full jitter: random value between 0 and delay
            delay = random.uniform(0.0, delay)
            
        return delay
