import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from realtime.sse.reconnect import ReconnectLoop
from realtime.retry.policy import RetryPolicy
from realtime.retry.types import RetryConfig

@pytest.mark.asyncio
async def test_reconnect_loop_success_first_attempt() -> None:
    policy = RetryPolicy()
    loop = ReconnectLoop(policy)
    
    connect_fn = AsyncMock(return_value=True)
    success = await loop.execute(connect_fn)
    
    assert success is True
    connect_fn.assert_called_once()
    assert policy.attempts == 0

@pytest.mark.asyncio
async def test_reconnect_loop_retry_and_exhaust() -> None:
    config = RetryConfig(max_attempts=3, initial_delay=0.01, backoff_factor=1.1, jitter=False)
    policy = RetryPolicy(config)
    loop = ReconnectLoop(policy)
    
    connect_fn = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), Exception("fail")])
    
    success = await loop.execute(connect_fn)
    assert success is False
    assert connect_fn.call_count == 3
