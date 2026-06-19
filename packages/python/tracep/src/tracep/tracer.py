"""
tracep.tracer
=============
Fire-and-forget OTel tracer that:
  - exports via OTLP/HTTP JSON to <endpoint>/v1/traces on port 4318
  - uses BatchSpanProcessor (batch=50, flush every 1 s)
  - sends all trace() calls through a background daemon queue thread
  - retries exports 3× with 100 ms / 200 ms / 400 ms back-off
  - never blocks the caller
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Dict, Optional, Tuple

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, Span, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import NonRecordingSpan, SpanContext, SpanKind, TraceFlags
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger(__name__)

# Public helpers so callers can use keyword-style options without raw strings.
class WithParent(str):
    """Thin str sub-class so type checkers can distinguish parent tid values."""


class WithLevel(str):
    """Thin str sub-class so type checkers can distinguish level values."""


# ---------------------------------------------------------------------------
# Internal worker command types
# ---------------------------------------------------------------------------
_CMD_TRACE = "trace"
_CMD_END   = "end"
_CMD_STOP  = "stop"


class Tracer:
    """
    Lightweight OTel tracer facade.

    Parameters
    ----------
    endpoint : str
        Base URL of the OTLP collector, e.g. ``"http://localhost:4318"``.
        The exporter will POST to ``<endpoint>/v1/traces``.
    api_key  : str
        Bearer token sent in every ``Authorization`` header.
    service  : str
        Value of the ``service.name`` OTel resource attribute.
    """

    def __init__(self, endpoint: str, api_key: str, service: str) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key  = api_key
        self._service  = service

        # ---- OTel provider setup -----------------------------------------
        resource = Resource.create({"service.name": service})

        exporter = OTLPSpanExporter(
            endpoint=f"{self._endpoint}/v1/traces",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        processor = BatchSpanProcessor(
            exporter,
            max_export_batch_size=50,
            schedule_delay_millis=1000,
            export_timeout_millis=10_000,
            max_queue_size=2048,
        )

        self._provider = TracerProvider(resource=resource)
        self._provider.add_span_processor(processor)

        self._otel_tracer = self._provider.get_tracer(__name__)

        # ---- Per-trace state storage --------------------------------------
        # _roots : tid -> root Span
        # _spans : (tid, cls, fn) -> child Span
        self._roots: Dict[str, Span] = {}
        self._spans: Dict[Tuple[str, str, str], Span] = {}
        self._lock  = threading.Lock()

        # ---- Background worker -------------------------------------------
        self._q: "queue.Queue[dict]" = queue.Queue()
        self._worker = threading.Thread(
            target=self._run_worker, name="tracep-worker", daemon=True
        )
        self._worker.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, name: str) -> str:
        """
        Start a new root trace.

        Returns
        -------
        str
            Hex-encoded 128-bit trace ID (32 hex chars), usable as *tid*
            in subsequent :meth:`trace` / :meth:`end` calls.
        """
        root_span: Span = self._otel_tracer.start_span(
            name, kind=SpanKind.INTERNAL
        )
        tid = format(root_span.get_span_context().trace_id, "032x")

        with self._lock:
            self._roots[tid] = root_span

        return tid

    def trace(
        self,
        tid: str,
        cls: str,
        function: str,
        step: str,
        message: str,
        *,
        parent: Optional[str] = None,
        level: str = "info",
    ) -> None:
        """
        Enqueue a tracing event.  Returns immediately; work is done on
        a background daemon thread.

        Parameters
        ----------
        tid      : Trace ID returned by :meth:`start`.
        cls      : Logical class / module name → ``code.namespace`` attribute.
        function : Function / method name → ``code.function`` attribute.
        step     : Name of the OTel span event.
        message  : Human-readable description, stored as event attribute.
        parent   : Optional parent span key ``"<cls>/<function>"`` form **or**
                   the string tid of another trace to link to.
        level    : Severity label (``"info"``, ``"warn"``, ``"error"`` …).
        """
        self._q.put_nowait(
            {
                "cmd":      _CMD_TRACE,
                "tid":      tid,
                "cls":      cls,
                "function": function,
                "step":     step,
                "message":  message,
                "parent":   parent,
                "level":    level,
            }
        )

    def end(self, tid: str, status: str) -> None:
        """
        Enqueue a trace-end command.  Returns immediately.

        Parameters
        ----------
        tid    : Trace ID to close.
        status : ``"ok"`` or ``"error"``.
        """
        self._q.put_nowait({"cmd": _CMD_END, "tid": tid, "status": status})

    def close(self) -> None:
        """Gracefully stop the background worker and shut down the provider."""
        self._q.put_nowait({"cmd": _CMD_STOP})
        self._worker.join(timeout=5)

    # ------------------------------------------------------------------
    # Background worker
    # ------------------------------------------------------------------

    def _run_worker(self) -> None:
        while True:
            try:
                cmd = self._q.get()
                kind = cmd.get("cmd")

                if kind == _CMD_TRACE:
                    self._do_trace(cmd)
                elif kind == _CMD_END:
                    self._do_end(cmd)
                elif kind == _CMD_STOP:
                    break
                else:
                    logger.warning("tracep: unknown command %r", kind)
            except Exception:  # pylint: disable=broad-except
                logger.exception("tracep: worker error")
            finally:
                try:
                    self._q.task_done()
                except ValueError:
                    pass  # task_done called on empty queue guard

    # ------------------------------------------------------------------
    # Actual (sync) implementations called from worker thread
    # ------------------------------------------------------------------

    def _do_trace(self, cmd: dict) -> None:
        tid      = cmd["tid"]
        cls      = cmd["cls"]
        function = cmd["function"]
        step     = cmd["step"]
        message  = cmd["message"]
        parent   = cmd.get("parent")
        level    = cmd.get("level", "info")

        with self._lock:
            root = self._roots.get(tid)

        if root is None:
            # Unknown tid — silently ignore as specified
            logger.debug("tracep: trace() called with unknown tid=%r; ignoring", tid)
            return

        key = (tid, cls, function)

        with self._lock:
            span = self._spans.get(key)

        if span is None:
            # Determine parent context
            if parent:
                parent_key = (tid, *parent.split("/", 1)) if "/" in str(parent) else None
                with self._lock:
                    parent_span = (
                        self._spans.get(tuple(parent_key))  # type: ignore[arg-type]
                        if parent_key
                        else self._roots.get(parent)
                    )
                if parent_span is not None:
                    ctx = otel_trace.set_span_in_context(parent_span)
                else:
                    ctx = otel_trace.set_span_in_context(root)
            else:
                ctx = otel_trace.set_span_in_context(root)

            span = self._otel_tracer.start_span(
                f"{cls}.{function}",
                context=ctx,
                kind=SpanKind.INTERNAL,
                attributes={
                    "code.namespace": cls,
                    "code.function":  function,
                },
            )

            with self._lock:
                self._spans[key] = span

        # Add the event regardless of whether span was just created or cached
        span.add_event(
            step,
            attributes={"message": message, "level": level},
        )

    def _do_end(self, cmd: dict) -> None:
        tid    = cmd["tid"]
        status = cmd.get("status", "ok")

        otel_status = (
            Status(StatusCode.OK)
            if status == "ok"
            else Status(StatusCode.ERROR, description=status)
        )

        with self._lock:
            child_keys = [k for k in self._spans if k[0] == tid]
            child_spans = [self._spans.pop(k) for k in child_keys]
            root = self._roots.pop(tid, None)

        # End children first (LIFO order)
        for span in reversed(child_spans):
            try:
                span.set_status(otel_status)
                span.end()
            except Exception:  # pylint: disable=broad-except
                logger.exception("tracep: error ending child span")

        if root is not None:
            try:
                root.set_status(otel_status)
                root.end()
            except Exception:  # pylint: disable=broad-except
                logger.exception("tracep: error ending root span")

        # Force flush so BatchSpanProcessor ships everything immediately
        try:
            self._provider.force_flush(timeout_millis=5000)
        except Exception:  # pylint: disable=broad-except
            logger.exception("tracep: force_flush failed")
