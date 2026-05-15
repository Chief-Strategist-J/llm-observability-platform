import asyncio
from typing import Any, Callable

async def execute_external_call_async(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Exactly one thing: the external call."""
    return await func(*args, **kwargs)

def execute_external_call_sync(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Exactly one thing: the external call."""
    return func(*args, **kwargs)
