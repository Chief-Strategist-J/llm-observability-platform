from typing import Protocol


class RedisPort(Protocol):
    def get_ewma(self, service: str, model: str, hour_of_week: int) -> float | None: ...

    def set_ewma(
        self, service: str, model: str, hour_of_week: int, value: float
    ) -> None: ...
