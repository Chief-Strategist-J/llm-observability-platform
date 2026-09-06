from dataclasses import dataclass

@dataclass
class RetryConfig:
    max_attempts: int = 5
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
