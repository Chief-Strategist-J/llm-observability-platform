from typing import Protocol, Union, List, Dict, Any, Tuple

class TokenCounterPort(Protocol):
    def count_tokens(self, prompt: Union[str, List[Dict[str, Any]]], model: str) -> Tuple[int, str]:
        ...

class ObservableSpanPort(Protocol):
    @property
    def _start_time(self) -> float:
        ...

    def set_metadata(self, key: str, value: Any) -> None:
        ...

    def finalize_stream(self, exc_type: Any = None) -> None:
        ...

    async def finalize_stream_async(self, exc_type: Any = None) -> None:
        ...
