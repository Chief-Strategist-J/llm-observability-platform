from realtime.retry.policy import RetryPolicy
from realtime.retry.types import RetryConfig

def test_retry_policy_exhaustion() -> None:
    config = RetryConfig(max_attempts=3, initial_delay=1.0, backoff_factor=2.0, jitter=False)
    policy = RetryPolicy(config)
    
    assert policy.next_delay() == 1.0
    assert policy.next_delay() == 2.0
    assert policy.next_delay() is None
    
    policy.reset()
    assert policy.attempts == 0
    assert policy.next_delay() == 1.0
