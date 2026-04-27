import time
import threading
from typing import Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from domain.ports.metrics_port import MetricsPort


@dataclass
class MetricSnapshot:
    timestamp: float
    value: float


@dataclass
class LatencyStats:
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    avg: float = 0.0


class MetricsCollector(MetricsPort):
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self._lock = threading.Lock()

        self._request_count: int = 0
        self._request_start_time: float = time.time()

        self._latencies: deque = deque(maxlen=window_size)
        self._queue_depths: deque = deque(maxlen=window_size)
        self._batch_sizes: deque = deque(maxlen=window_size)
        self._flush_durations: deque = deque(maxlen=window_size)
        self._postgres_write_times: deque = deque(maxlen=window_size)
        self._mongo_write_times: deque = deque(maxlen=window_size)
        self._kafka_produce_times: deque = deque(maxlen=window_size)
        self._pool_wait_times: deque = deque(maxlen=window_size)

        self._rejected_requests: int = 0
        self._total_requests: int = 0

        self._per_shard_batch_sizes: Dict[Tuple[int, int], deque] = {}
        self._per_shard_flush_durations: Dict[Tuple[int, int], deque] = {}

    def record_request(self) -> None:
        with self._lock:
            self._request_count += 1
            self._total_requests += 1

    def record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._latencies.append(latency_ms)

    def record_queue_depth(self, depth: int) -> None:
        with self._lock:
            self._queue_depths.append(depth)

    def record_batch_size(self, size: int) -> None:
        with self._lock:
            self._batch_sizes.append(size)

    def record_flush_duration(self, duration_ms: float, shard_key: Optional[Tuple[int, int]] = None) -> None:
        with self._lock:
            self._flush_durations.append(duration_ms)
            if shard_key:
                if shard_key not in self._per_shard_flush_durations:
                    self._per_shard_flush_durations[shard_key] = deque(maxlen=self.window_size)
                self._per_shard_flush_durations[shard_key].append(duration_ms)

    def record_postgres_write_time(self, duration_ms: float) -> None:
        with self._lock:
            self._postgres_write_times.append(duration_ms)

    def record_mongo_write_time(self, duration_ms: float) -> None:
        with self._lock:
            self._mongo_write_times.append(duration_ms)

    def record_kafka_produce_time(self, duration_ms: float) -> None:
        with self._lock:
            self._kafka_produce_times.append(duration_ms)

    def record_pool_wait_time(self, duration_ms: float) -> None:
        with self._lock:
            self._pool_wait_times.append(duration_ms)

    def record_rejection(self) -> None:
        with self._lock:
            self._rejected_requests += 1

    def record_shard_batch_size(self, size: int, shard_key: Tuple[int, int]) -> None:
        with self._lock:
            if shard_key not in self._per_shard_batch_sizes:
                self._per_shard_batch_sizes[shard_key] = deque(maxlen=self.window_size)
            self._per_shard_batch_sizes[shard_key].append(size)

    def get_request_rate(self) -> float:
        with self._lock:
            elapsed = time.time() - self._request_start_time
            return self._request_count / elapsed if elapsed > 0 else 0.0

    def get_latency_stats(self) -> LatencyStats:
        with self._lock:
            if not self._latencies:
                return LatencyStats()

            sorted_latencies = sorted(self._latencies)
            n = len(sorted_latencies)
            return LatencyStats(
                p50=sorted_latencies[n // 2],
                p95=sorted_latencies[int(n * 0.95)],
                p99=sorted_latencies[int(n * 0.99)],
                avg=sum(sorted_latencies) / n
            )

    def get_current_queue_depth(self) -> int:
        with self._lock:
            return self._queue_depths[-1] if self._queue_depths else 0

    def get_avg_batch_size(self) -> float:
        with self._lock:
            if not self._batch_sizes:
                return 0.0
            return sum(self._batch_sizes) / len(self._batch_sizes)

    def get_avg_flush_duration(self) -> float:
        with self._lock:
            if not self._flush_durations:
                return 0.0
            return sum(self._flush_durations) / len(self._flush_durations)

    def get_avg_postgres_write_time(self) -> float:
        with self._lock:
            if not self._postgres_write_times:
                return 0.0
            return sum(self._postgres_write_times) / len(self._postgres_write_times)

    def get_avg_mongo_write_time(self) -> float:
        with self._lock:
            if not self._mongo_write_times:
                return 0.0
            return sum(self._mongo_write_times) / len(self._mongo_write_times)

    def get_avg_kafka_produce_time(self) -> float:
        with self._lock:
            if not self._kafka_produce_times:
                return 0.0
            return sum(self._kafka_produce_times) / len(self._kafka_produce_times)

    def get_avg_pool_wait_time(self) -> float:
        with self._lock:
            if not self._pool_wait_times:
                return 0.0
            return sum(self._pool_wait_times) / len(self._pool_wait_times)

    def get_rejection_rate(self) -> float:
        with self._lock:
            if self._total_requests == 0:
                return 0.0
            return self._rejected_requests / self._total_requests

    def get_per_shard_stats(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            stats = {}
            for shard_key, batch_sizes in self._per_shard_batch_sizes.items():
                key_str = f"{shard_key[0]}-{shard_key[1]}"
                stats[key_str] = {
                    "avg_batch_size": sum(batch_sizes) / len(batch_sizes) if batch_sizes else 0.0,
                    "avg_flush_duration": 0.0
                }
                if shard_key in self._per_shard_flush_durations:
                    flush_durations = self._per_shard_flush_durations[shard_key]
                    stats[key_str]["avg_flush_duration"] = sum(flush_durations) / len(flush_durations) if flush_durations else 0.0
            return stats

    def get_alerts(self) -> List[str]:
        alerts = []
        queue_depth = self.get_current_queue_depth()
        rejection_rate = self.get_rejection_rate()
        avg_flush_duration = self.get_avg_flush_duration()

        if queue_depth > 80000:
            alerts.append(f"Queue depth critical: {queue_depth}")

        if avg_flush_duration > 50:
            alerts.append(f"Flush duration high: {avg_flush_duration:.2f}ms")

        if rejection_rate > 0.05:
            alerts.append(f"Rejection rate high: {rejection_rate:.2%}")

        per_shard_stats = self.get_per_shard_stats()
        avg_flush = self.get_avg_flush_duration()
        for shard_key, stats in per_shard_stats.items():
            if stats["avg_flush_duration"] > avg_flush * 2:
                alerts.append(f"Shard {shard_key} lagging: {stats['avg_flush_duration']:.2f}ms")

        return alerts

    def get_all_metrics(self) -> Dict:
        latency_stats = self.get_latency_stats()
        return {
            "request_rate": self.get_request_rate(),
            "latency": {
                "p50_ms": latency_stats.p50,
                "p95_ms": latency_stats.p95,
                "p99_ms": latency_stats.p99,
                "avg_ms": latency_stats.avg
            },
            "queue_depth": self.get_current_queue_depth(),
            "batch_size": {
                "avg": self.get_avg_batch_size()
            },
            "flush_duration_ms": self.get_avg_flush_duration(),
            "postgres_write_time_ms": self.get_avg_postgres_write_time(),
            "mongo_write_time_ms": self.get_avg_mongo_write_time(),
            "kafka_produce_time_ms": self.get_avg_kafka_produce_time(),
            "pool_wait_time_ms": self.get_avg_pool_wait_time(),
            "rejection_rate": self.get_rejection_rate(),
            "rejected_count": self._rejected_requests,
            "total_requests": self._total_requests,
            "per_shard_stats": self.get_per_shard_stats(),
            "alerts": self.get_alerts(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def reset(self) -> None:
        with self._lock:
            self._request_count = 0
            self._request_start_time = time.time()
            self._latencies.clear()
            self._queue_depths.clear()
            self._batch_sizes.clear()
            self._flush_durations.clear()
            self._postgres_write_times.clear()
            self._mongo_write_times.clear()
            self._kafka_produce_times.clear()
            self._pool_wait_times.clear()
            self._rejected_requests = 0
            self._total_requests = 0
            self._per_shard_batch_sizes.clear()
            self._per_shard_flush_durations.clear()
