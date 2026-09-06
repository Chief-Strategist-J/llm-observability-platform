import asyncio
from typing import Any, Callable, Dict

async def execute_external_call_async(func: Callable, *args: Any, **kwargs: Any) -> Any:
    return await func(*args, **kwargs)

def execute_external_call_sync(func: Callable, *args: Any, **kwargs: Any) -> Any:
    return func(*args, **kwargs)

def apply_metadata_pipe(span: Any, metadata: Dict[str, Any]) -> None:
    list(map(lambda item: span.set_metadata(item[0], item[1]), metadata.items()))
