import asyncio
import logging
from typing import Callable, Awaitable
from realtime.retry.policy import RetryPolicy

logger = logging.getLogger(__name__)

class ReconnectLoop:
    def __init__(self, retry_policy: RetryPolicy) -> None:
        self.policy = retry_policy

    async def execute(self, connect_fn: Callable[[], Awaitable[bool]]) -> bool:
        """Execute the reconnect loop by calling connect_fn. Delegates delays to retry policy."""
        self.policy.reset()
        while True:
            try:
                success = await connect_fn()
                if success:
                    self.policy.reset()
                    return True
            except Exception as e:
                logger.warning("Connection attempt failed: %s", e)

            delay = self.policy.next_delay()
            if delay is None:
                logger.error("Reconnect attempts exhausted.")
                return False

            logger.info("Retrying connection in %s seconds...", delay)
            await asyncio.sleep(delay)
