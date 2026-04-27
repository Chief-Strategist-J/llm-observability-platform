from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class MetricsPort(ABC):
    @abstractmethod
    def record_request(self) -> None:
        pass

    @abstractmethod
    def record_latency(self, latency_ms: float) -> None:
        pass

    @abstractmethod
    def record_queue_depth(self, depth: int) -> None:
        pass

    @abstractmethod
    def record_batch_size(self, size: int) -> None:
        pass

    @abstractmethod
    def record_flush_duration(self, duration_ms: float, shard_key: Tuple[int, int] = None) -> None:
        pass

    @abstractmethod
    def record_rejection(self) -> None:
        pass

    @abstractmethod
    def get_all_metrics(self) -> Dict:
        pass
