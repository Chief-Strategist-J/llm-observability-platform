import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional
from temporalio import activity

from infrastructure.observability_platform.ingest.application_stdout.model.config_model import FileConfigStore
from infrastructure.observability_platform.ingest.application_stdout.service.log_discovery_service import LocalLogDiscoveryService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShipRuntime:
    files: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    protocol: str = ""
    endpoint: str = ""
    batch_size: int = 100
    flush_interval_seconds: int = 5
    timeout_seconds: int = 10
    config_path: str = "infrastructure/observability_platform/ingest/config/log_discovery_config.yaml"


class PayloadFormats:
    def build_loki(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        streams = {}
        for rec in records:
            key = json.dumps(rec["labels"], sort_keys=True)
            streams.setdefault(key, []).append([str(rec["ts_unix_ns"]), rec["line"]])
        return {"streams": [{"stream": json.loads(k), "values": v} for k, v in streams.items()]}

    def build_otlp(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        logs = []
        for rec in records:
            attributes = [{"key": k, "value": {"stringValue": v}} for k, v in rec["labels"].items()]
            logs.append({
                "timeUnixNano": str(rec["ts_unix_ns"]),
                "body": {"stringValue": rec["line"]},
                "attributes": attributes,
                "severityNumber": 9,
                "severityText": "INFO"
            })
        return {
            "resourceLogs": [{
                "resource": {
                    "attributes": attributes
                },
                "scopeLogs": [{
                    "logRecords": logs
                }]
            }]
        }


class ShipperFactory:
    def create(self, protocol: str, endpoint: str, timeout: int) -> Callable[[List[Dict[str, Any]]], asyncio.Future]:
        proto = (protocol or "").strip().lower()
        ep = (endpoint or "").strip()
        builder = PayloadFormats()

        if not proto or not ep:
            async def noop_send(_batch: List[Dict[str, Any]]):
                logger.info("shipping disabled: protocol or endpoint not configured")
                return None
            return noop_send

        if proto == "loki":
            async def loki_send(batch: List[Dict[str, Any]]):
                payload = builder.build_loki(batch)
                await self._safe_post(ep.rstrip("/") + "/loki/api/v1/push", payload, timeout)
            return loki_send

        if proto == "otlp":
            async def otlp_send(batch: List[Dict[str, Any]]):
                payload = builder.build_otlp(batch)
                await self._safe_post(ep.rstrip("/") + "/v1/logs", payload, timeout)
            return otlp_send

        async def unsupported(_):
            logger.warning("Unsupported protocol requested: %s", proto)
            return None

        return unsupported

    async def _safe_post(self, endpoint: str, payload: Dict[str, Any], timeout: int):
        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=timeout))
            logger.debug("successfully sent batch to %s", endpoint)
        except Exception as e:
            logger.warning("failed to send to endpoint %s: %s", endpoint, e, exc_info=False)


class FileTailer:
    def __init__(self, paths: List[str], callback: Callable[[Dict[str, Any]], None]):
        self.paths = paths
        self.callback = callback
        self.tasks: List[asyncio.Task] = []

    async def start(self):
        for path in self.paths:
            t = asyncio.create_task(self._tail(path))
            self.tasks.append(t)

    async def wait(self):
        if self.tasks:
            await asyncio.gather(*self.tasks)

    async def _tail(self, path: str):
        try:
            f = open(path, "r", encoding="utf-8", errors="ignore")
        except PermissionError:
            logger.warning("permission denied skipping path=%s", path)
            return
        except FileNotFoundError:
            logger.warning("file not found skipping path=%s", path)
            return
        try:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.15)
                    continue
                rec = {"path": path, "line": line.rstrip("\n"), "ts_unix_ns": time.time_ns()}
                self.callback(rec)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.error("tail error path=%s", path, exc_info=True)


class LogBatcher:
    def __init__(self, size: int, interval: int, send_func: Callable[[List[Dict[str, Any]]], asyncio.Future]):
        self.size = size
        self.interval = interval
        self.send_func = send_func
        self.buffer: List[Dict[str, Any]] = []
        self.last_flush = time.time()
        self.lock = asyncio.Lock()

    async def add(self, record: Dict[str, Any], labels: Dict[str, str]):
        entry = {
            "path": record["path"],
            "line": record["line"],
            "labels": labels,
            "ts_unix_ns": record["ts_unix_ns"],
        }
        async with self.lock:
            self.buffer.append(entry)
            if len(self.buffer) >= self.size:
                await self.flush()

    async def flush(self):
        async with self.lock:
            if not self.buffer:
                return
            batch = self.buffer
            self.buffer = []
        try:
            await self.send_func(batch)
        except Exception:
            logger.error("batch send failed", exc_info=True)
        self.last_flush = time.time()

    async def periodic(self):
        try:
            while True:
                await asyncio.sleep(1)
                if self.buffer and (time.time() - self.last_flush) >= self.interval:
                    await self.flush()
        except asyncio.CancelledError:
            return


class TailAndShipService:
    async def run(self, runtime: ShipRuntime):
        config = FileConfigStore(runtime.config_path).ensure_exists()
        files = runtime.files or LocalLogDiscoveryService(config).discover()
        labels = runtime.labels or dict(config.labels.values)

        send_func = ShipperFactory().create(runtime.protocol, runtime.endpoint, runtime.timeout_seconds)
        batcher = LogBatcher(runtime.batch_size, runtime.flush_interval_seconds, send_func)

        queue: asyncio.Queue = asyncio.Queue()

        def enqueue(rec: Dict[str, Any]):
            try:
                queue.put_nowait(rec)
            except asyncio.QueueFull:
                logger.warning("queue full, dropping record path=%s", rec.get("path"))

        tailer = FileTailer(files, enqueue)
        await tailer.start()

        async def consume():
            try:
                while True:
                    rec = await queue.get()
                    await batcher.add(rec, labels)
            except asyncio.CancelledError:
                return

        consumer_task = asyncio.create_task(consume())
        periodic_task = asyncio.create_task(batcher.periodic())

        try:
            await asyncio.gather(tailer.wait(), consumer_task, periodic_task)
        except asyncio.CancelledError:
            consumer_task.cancel()
            periodic_task.cancel()
            return


_background_task = None


@activity.defn
async def tail_and_ship_logs_activity(params: dict) -> dict:
    global _background_task

    runtime = ShipRuntime(
        files=params.get("files", []),
        labels=params.get("labels", {}),
        protocol=params.get("protocol", "otlp"),
        endpoint=params.get("endpoint", "http://localhost:4318"),
        batch_size=params.get("batch_size", 100),
        flush_interval_seconds=params.get("flush_interval_seconds", 5),
        timeout_seconds=params.get("timeout_seconds", 10),
    )

    service = TailAndShipService()
    _background_task = asyncio.create_task(service.run(runtime))

    logger.info("tail_and_ship_logs_activity started in background for %d files", len(runtime.files))

    return {
        "status": "started",
        "files_count": len(runtime.files),
        "protocol": runtime.protocol,
        "endpoint": runtime.endpoint
    }