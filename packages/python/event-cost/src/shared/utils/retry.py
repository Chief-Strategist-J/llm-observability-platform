import time
from typing import Callable, TypeVar
from shared.types.cost_types import ProcessingError

T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    max_retries: int = 3,
    base_ms: int = 100,
) -> T:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            delay_s = (base_ms * (2 ** attempt)) / 1000.0
            time.sleep(delay_s)
    raise ProcessingError(
        f"Failed after {max_retries} retries"
    ) from last_error
