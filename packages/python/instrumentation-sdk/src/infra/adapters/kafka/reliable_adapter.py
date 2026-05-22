import json
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Tuple
from google.protobuf import json_format
from src.features.spans.reporter import SpanReporter
from src.shared.ports.kafka import KafkaProducerPort
from src.shared.ports.wal import WalStoragePort
from src.infra.adapters.kafka.confluent_producer_adapter import ConfluentKafkaProducerAdapter
from src.infra.adapters.wal.sqlite_wal_adapter import SqliteWalStorageAdapter
from src.infra.clients.v1.llm.observability.v1.span_pb2 import LLMSpan

class ReliableKafkaSpanReporter(SpanReporter):
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "llm.spans.raw",
        wal_path: str = "/tmp/llm-obs-wal.db",
        max_buffer_size: int = 100000,
        producer_port: Optional[KafkaProducerPort] = None,
        wal_port: Optional[WalStoragePort] = None
    ) -> None:
        self.topic = topic
        self._queue: queue.Queue[Tuple[str, bytes, Dict[str, Any]]] = queue.Queue(maxsize=max_buffer_size)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        if producer_port is None:
            self._producer_port: KafkaProducerPort = ConfluentKafkaProducerAdapter(bootstrap_servers)
        else:
            self._producer_port = producer_port
            
        if wal_port is None:
            self._wal_port: WalStoragePort = SqliteWalStorageAdapter(wal_path)
        else:
            self._wal_port = wal_port

        self._wal_port.initialize()
        
        try:
            self._is_online = self._producer_port.check_availability()
        except Exception:
            self._is_online = False
        self._wal_has_pending = False
        self._active_wal_writes = 0
        
        try:
            initial_batch = self._wal_port.fetch_batch(1)
            if initial_batch:
                self._wal_has_pending = True
        except Exception:
            pass

        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def report(self, span_data: Dict[str, Any]) -> None:
        try:
            span_id = span_data["span_id"]
            span_bytes = self._dict_to_proto_bytes(span_data)
            
            write_wal_sync = False
            with self._lock:
                if self._is_online and not self._wal_has_pending:
                    try:
                        self._queue.put_nowait((span_id, span_bytes, span_data))
                        return
                    except queue.Full:
                        self._wal_has_pending = True
                
                try:
                    self._queue.put_nowait((span_id, span_bytes, span_data))
                except queue.Full:
                    write_wal_sync = True
                    self._active_wal_writes += 1

            if write_wal_sync:
                try:
                    self._wal_port.save(span_id, span_bytes)
                    with self._lock:
                        self._wal_has_pending = True
                finally:
                    with self._lock:
                        self._active_wal_writes -= 1
        except Exception:
            pass

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.report(span_data)

    def close(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)
        try:
            self._producer_port.flush(timeout)
        except Exception:
            pass

    def _dict_to_proto_bytes(self, span_data: Dict[str, Any]) -> bytes:
        d = dict(span_data)
        if "environment" in d and d["environment"]:
            env = str(d["environment"]).upper()
            d["environment"] = f"ENVIRONMENT_{env}"
        if "finish_reason" in d and d["finish_reason"]:
            fr = str(d["finish_reason"]).upper()
            d["finish_reason"] = f"FINISH_REASON_{fr}"
        if "token_count_method" in d and d["token_count_method"]:
            tcm = str(d["token_count_method"]).upper()
            d["token_count_method"] = f"TOKEN_COUNT_METHOD_{tcm}"
        if "timestamp_utc" in d and not isinstance(d["timestamp_utc"], str):
            d["timestamp_utc"] = d["timestamp_utc"].isoformat()
        for uuid_field in ["span_id", "trace_id", "parent_span_id"]:
            if uuid_field in d and d[uuid_field] is not None:
                d[uuid_field] = str(d[uuid_field])
        
        proto_span = LLMSpan()
        json_format.ParseDict(d, proto_span)
        return proto_span.SerializeToString()

    def _make_delivery_callback(self, db_id: Optional[int], span_id: str, span_bytes: bytes) -> Callable[[Any, Any], None]:
        def callback(err: Any, msg: Any) -> None:
            try:
                if err is not None:
                    with self._lock:
                        self._is_online = False
                    if db_id is None:
                        try:
                            self._wal_port.save(span_id, span_bytes)
                            with self._lock:
                                self._wal_has_pending = True
                        except Exception:
                            pass
                else:
                    with self._lock:
                        self._is_online = True
                    if db_id is not None:
                        try:
                            self._wal_port.delete_batch([db_id])
                        except Exception:
                            pass
            except Exception:
                pass
        return callback

    def _replay_wal(self) -> None:
        while True:
            with self._lock:
                if not self._is_online:
                    break
            
            try:
                batch = self._wal_port.fetch_batch(100)
            except Exception:
                break
                
            if not batch:
                with self._lock:
                    if self._active_wal_writes == 0:
                        try:
                            double_check = self._wal_port.fetch_batch(1)
                            if not double_check:
                                self._wal_has_pending = False
                                break
                        except Exception:
                            pass
                continue

            for db_id, span_id, span_bytes in batch:
                try:
                    callback = self._make_delivery_callback(db_id, span_id, span_bytes)
                    self._producer_port.produce(self.topic, key=span_id, value=span_bytes, on_delivery=callback)
                except Exception:
                    try:
                        self._wal_port.delete_batch([db_id])
                    except Exception:
                        pass
            
            try:
                self._producer_port.flush(5.0)
            except Exception:
                pass

    def _worker_loop(self) -> None:
        last_availability_check = 0.0
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                current_time = time.time()
                with self._lock:
                    online = self._is_online
                    has_pending = self._wal_has_pending

                if not online:
                    drained: List[Tuple[str, bytes, Dict[str, Any]]] = []
                    while not self._queue.empty():
                        try:
                            drained.append(self._queue.get_nowait())
                        except queue.Empty:
                            break
                    if drained:
                        batch = [(span_id, span_bytes) for span_id, span_bytes, _ in drained]
                        try:
                            self._wal_port.save_batch(batch)
                        except Exception:
                            pass
                        with self._lock:
                            self._wal_has_pending = True

                    if current_time - last_availability_check >= 5.0:
                        last_availability_check = current_time
                        if self._producer_port.check_availability():
                            with self._lock:
                                self._is_online = True
                            continue

                    time.sleep(0.1)
                    continue

                if has_pending:
                    self._replay_wal()
                    continue

                try:
                    item = self._queue.get(timeout=0.1)
                    span_id, span_bytes, span_data = item
                    with self._lock:
                        if self._wal_has_pending:
                            self._queue.put(item)
                            continue

                    try:
                        callback = self._make_delivery_callback(None, span_id, span_bytes)
                        self._producer_port.produce(
                            self.topic,
                            key=span_id,
                            value=span_bytes,
                            on_delivery=callback
                        )
                    except Exception:
                        try:
                            self._wal_port.save(span_id, span_bytes)
                            with self._lock:
                                self._wal_has_pending = True
                        except Exception:
                            pass

                    self._producer_port.poll(0)
                except queue.Empty:
                    self._producer_port.poll(0.01)

            except Exception:
                pass
