import time
import logging
from typing import Callable, Any, TypeVar, Tuple, Type

T = TypeVar("T")
logger = logging.getLogger("python_shared.http.resilience.retry")

class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise e
                backoff = self.backoff_factor * (2 ** (attempt - 1))
                logger.warning(f"Retry attempt {attempt}/{self.max_retries} after {backoff}s due to: {e}")
                time.sleep(backoff)

    async def execute_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        import asyncio
        attempt = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise e
                backoff = self.backoff_factor * (2 ** (attempt - 1))
                logger.warning(f"Async retry attempt {attempt}/{self.max_retries} after {backoff}s due to: {e}")
                await asyncio.sleep(backoff)
