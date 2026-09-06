from realtime.retry.backoff import Backoff
from realtime.retry.types import RetryConfig

def test_backoff_calculate_delay_no_jitter() -> None:
    config = RetryConfig(initial_delay=1.0, backoff_factor=2.0, max_delay=10.0, jitter=False)
    
    assert Backoff.calculate_delay(0, config) == 0.0
    assert Backoff.calculate_delay(1, config) == 1.0
    assert Backoff.calculate_delay(2, config) == 2.0
    assert Backoff.calculate_delay(3, config) == 4.0
    assert Backoff.calculate_delay(4, config) == 8.0
    assert Backoff.calculate_delay(5, config) == 10.0  # Max delay capped

def test_backoff_calculate_delay_jitter() -> None:
    config = RetryConfig(initial_delay=1.0, backoff_factor=2.0, max_delay=10.0, jitter=True)
    
    for attempt in range(1, 6):
        delay = Backoff.calculate_delay(attempt, config)
        max_possible = min(config.initial_delay * (config.backoff_factor ** (attempt - 1)), config.max_delay)
        assert 0.0 <= delay <= max_possible
