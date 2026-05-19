import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from opentelemetry import trace
from ..spans.index import LLMSpan, FinishReason, TokenCountMethod, Environment
from ..spans.globals import get_reporter

class LLMSpanContext:
    def __init__(self, **kwargs: Any):
        self._span_id = uuid.uuid4()
        self._start_time = time.perf_counter()
        pii_detected = False
        injection_attempt = False
        prompt = kwargs.get("prompt")
        if prompt is not None:
            try:
                from ..pii_injection_scan.index import scan_prompt
                pii_detected, injection_attempt = scan_prompt(prompt)
                if pii_detected:
                    kwargs["prompt"] = None
                    if "prompt_hash" in kwargs:
                        kwargs["prompt_hash"] = None
                    if "prompt_embedding" in kwargs:
                        kwargs["prompt_embedding"] = None
                    if "response_embedding" in kwargs:
                        kwargs["response_embedding"] = None
            except Exception:
                pass
        self._data: Dict[str, Any] = {
            "span_id": self._span_id,
            "timestamp_utc": datetime.now(timezone.utc),
            "status": "success",
            "pii_detected": pii_detected,
            "injection_attempt": injection_attempt,
            **kwargs
        }
        self._otel_span = None
        self._otel_context = None

    def set_metadata(self, key: str, value: Any) -> None:
        if key == "prompt" and value is not None:
            try:
                from ..pii_injection_scan.index import scan_prompt
                pii_detected, injection_attempt = scan_prompt(value)
                self._data["pii_detected"] = pii_detected or self._data.get("pii_detected", False)
                self._data["injection_attempt"] = injection_attempt or self._data.get("injection_attempt", False)
                if pii_detected:
                    self._data["prompt"] = None
                    if "prompt_hash" in self._data:
                        self._data["prompt_hash"] = None
                    if "prompt_embedding" in self._data:
                        self._data["prompt_embedding"] = None
                    if "response_embedding" in self._data:
                        self._data["response_embedding"] = None
                    if self._otel_span and self._otel_span.is_recording():
                        self._otel_span.set_attribute("llm.pii_detected", True)
                        self._otel_span.set_attribute("llm.prompt_hash", "")
                        self._otel_span.set_attribute("llm.prompt_embedding", "")
                        self._otel_span.set_attribute("llm.response_embedding", "")
                    return
            except Exception:
                pass
        self._data[key] = value
        if self._otel_span and self._otel_span.is_recording():
            if isinstance(value, (str, bool, int, float)):
                self._otel_span.set_attribute(f"llm.{key}", value)

    def __enter__(self) -> 'LLMSpanContext':
        tracer = trace.get_tracer("instrumentation-sdk")
        span_name = self._data.get("span_type", "llm_call")
        self._otel_span = tracer.start_span(span_name)
        for k, v in self._data.items():
            if isinstance(v, (str, bool, int, float)):
                self._otel_span.set_attribute(f"llm.{k}", v)
        self._otel_context = trace.use_span(self._otel_span, end_on_exit=True)
        self._otel_context.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._finish(exc_type)
        if self._otel_span:
            if exc_type:
                self._otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            else:
                self._otel_span.set_status(trace.Status(trace.StatusCode.OK))
            latency_ms = self._data.get("latency_ms_total", 0)
            self._otel_span.set_attribute("llm.latency_ms_total", latency_ms)
            self._otel_span.set_attribute("llm.status", self._data["status"])
            self._otel_context.__exit__(exc_type, exc_val, exc_tb)
        reporter = get_reporter()
        reporter.report(self._data)

    async def __aenter__(self) -> 'LLMSpanContext':
        tracer = trace.get_tracer("instrumentation-sdk")
        span_name = self._data.get("span_type", "llm_call")
        self._otel_span = tracer.start_span(span_name)
        for k, v in self._data.items():
            if isinstance(v, (str, bool, int, float)):
                self._otel_span.set_attribute(f"llm.{k}", v)
        self._otel_context = trace.use_span(self._otel_span, end_on_exit=True)
        self._otel_context.__enter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._finish(exc_type)
        if self._otel_span:
            if exc_type:
                self._otel_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            else:
                self._otel_span.set_status(trace.Status(trace.StatusCode.OK))
            latency_ms = self._data.get("latency_ms_total", 0)
            self._otel_span.set_attribute("llm.latency_ms_total", latency_ms)
            self._otel_span.set_attribute("llm.status", self._data["status"])
            self._otel_context.__exit__(exc_type, exc_val, exc_tb)
        reporter = get_reporter()
        await reporter.report_async(self._data)

    def _finish(self, exc_type: Any) -> None:
        latency_ms = int((time.perf_counter() - self._start_time) * 1000)
        self._data["latency_ms_total"] = latency_ms
        if exc_type:
            self._data["status"] = "error"

def llm_span(**kwargs: Any) -> LLMSpanContext:
    return LLMSpanContext(**kwargs)
