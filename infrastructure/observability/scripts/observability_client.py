import logging
import time
import requests
import os
from typing import Optional, Dict, Iterable, Any, Generator
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.metrics import set_meter_provider, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
import inspect
import functools
import json

def trace_with_details(tracer, name_override=None):
    """
    Decorator to provide deep tracing including file path, line number, arguments, 
    and detailed exception capturing.
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name_override or func.__name__
            with tracer.start_as_current_span(span_name) as span:
                _capture_details(span, func, args, kwargs)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    _record_exception_details(span, e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name_override or func.__name__
            with tracer.start_as_current_span(span_name) as span:
                _capture_details(span, func, args, kwargs)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _record_exception_details(span, e)
                    raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

def _capture_details(span, func, args, kwargs):
    try:
        file_name = inspect.getsourcefile(func) or "unknown"
        lines = inspect.getsourcelines(func)
        line_no = lines[1] if lines else 0
        
        span.set_attribute("code.filepath", file_name)
        span.set_attribute("code.lineno", line_no)
        span.set_attribute("code.function", func.__name__)
        
        # safely capture args
        safe_args = [str(a)[:500] for a in args]
        safe_kwargs = {k: str(v)[:500] for k, v in kwargs.items()}
        span.set_attribute("fn.args", str(safe_args))
        span.set_attribute("fn.kwargs", str(safe_kwargs))
    except Exception as e:
        span.set_attribute("trace.meta.error", str(e))

def _record_exception_details(span, e):
    span.record_exception(e)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
    # Inspect usage stack 
    frame = inspect.currentframe()
    if frame and frame.f_back:
        span.set_attribute("error.caught_at_lineno", frame.f_back.f_lineno)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("ObservabilityClient")

class ObservabilityClient:
    def __init__(self, endpoint: str = "http://172.28.0.10:4317", service_name: str = "observability-test"):
        self.endpoint = endpoint
        self.service_name = service_name
        self.resource = Resource.create({"service.name": service_name})
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, Any] = {}
        
        try:
            self.setup_tracing()
            self.setup_logging()
            self.setup_metrics()
            _logger.info("ObservabilityClient initialized successfully")
        except Exception as e:
            _logger.error(f"Failed to initialize ObservabilityClient: {e}")
            raise

    def setup_tracing(self):
        try:
            self.trace_provider = TracerProvider(resource=self.resource)
            exporter = OTLPSpanExporter(endpoint=self.endpoint, insecure=True)
            self.trace_provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(self.trace_provider)
            self.tracer = trace.get_tracer(self.service_name)
        except Exception as e:
            _logger.error(f"Error setting up tracing: {e}")
            raise

    def setup_logging(self):
        try:
            logger_provider = LoggerProvider(resource=self.resource)
            exporter = OTLPLogExporter(endpoint=self.endpoint, insecure=True)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
            set_logger_provider(logger_provider)
            handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
            self.logger = logging.getLogger(self.service_name)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        except Exception as e:
            _logger.error(f"Error setting up logging: {e}")
            raise

    def setup_metrics(self):
        try:
            reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=self.endpoint, insecure=True),
                export_interval_millis=5000 
            )
            provider = MeterProvider(resource=self.resource, metric_readers=[reader])
            set_meter_provider(provider)
            self.meter = provider.get_meter(self.service_name)
            self.counter = self.meter.create_counter("test_counter", description="Test counter")
        except Exception as e:
            _logger.error(f"Error setting up metrics: {e}")
            raise

    def log_info(self, msg: str, attributes: Optional[Dict] = None):
        try:
            self.logger.info(msg, extra=attributes, stacklevel=2)
        except Exception as e:
            _logger.error(f"Failed to send info log: {e}")

    def log_error(self, msg: str, attributes: Optional[Dict] = None):
        try:
            self.logger.error(msg, extra=attributes, stacklevel=2)
        except Exception as e:
            _logger.error(f"Failed to send error log: {e}")

    def increment_counter(self, name: str, amount: int = 1, attributes: Optional[Dict] = None):
        try:
            if not hasattr(self, f"_cnt_{name}"):
                setattr(self, f"_cnt_{name}", self.meter.create_counter(name))
            getattr(self, f"_cnt_{name}").add(amount, attributes or {})
        except Exception as e:
            _logger.error(f"Failed to increment counter {name}: {e}")

    def record_gauge(self, name: str, value: float, attributes: Optional[Dict] = None):
        try:
            if name not in self._gauges:
                self._gauges[name] = value
                def _cb(opts: object) -> Iterable[Observation]:
                    yield Observation(self._gauges.get(name, 0), attributes or {})
                self.meter.create_observable_gauge(name, callbacks=[_cb])
            else:
                self._gauges[name] = value
        except Exception as e:
            _logger.error(f"Failed to record gauge {name}: {e}")

    def record_histogram(self, name: str, value: float, attributes: Optional[Dict] = None):
        try:
            if name not in self._histograms:
                self._histograms[name] = self.meter.create_histogram(name)
            self._histograms[name].record(value, attributes or {})
        except Exception as e:
            _logger.error(f"Failed to record histogram {name}: {e}")

    def instrument_mongodb(self):
        try:
            PymongoInstrumentor().instrument()
            _logger.info("Official MongoDB instrumentation enabled")
        except Exception as e:
            _logger.error(f"Failed to instrument MongoDB: {e}")

    def run_standard_test(self):
        try:
            _logger.info("Running standard verification test")
            with self.tracer.start_as_current_span("standard_test") as span:
                span.set_attribute("test.id", "standard-run")
                self.log_info("Standard test running", {"status": "active"})
                self.increment_counter("op_count", 1, {"action": "test"})
                self.record_gauge("system_health", 1.0)
                self.record_histogram("request_latency", 0.5)
                time.sleep(0.5)
            _logger.info("Standard test completed")
        except Exception as e:
            _logger.error(f"Standard test failed: {e}")

class ObservabilityVerifier:
    def __init__(self, base_url: str = "https://scaibu.grafana"):
        self.base_url = base_url
        self.auth = ("admin", "SuperSecret123!")
        self.verify = False 

    def query_prometheus(self, query: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/datasources/proxy/uid/prometheus/api/v1/query"
            response = requests.get(url, params={"query": query}, auth=self.auth, verify=self.verify)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Prometheus query failed: {e}")
            raise

    def query_loki(self, query: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/datasources/proxy/uid/loki/loki/api/v1/query_range"
            response = requests.get(url, params={"query": query}, auth=self.auth, verify=self.verify)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Loki query failed: {e}")
            raise

    def query_traces(self, service: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/datasources/proxy/uid/jaeger/api/traces"
            response = requests.get(url, params={"service": service}, auth=self.auth, verify=self.verify)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Jaeger query failed: {e}")
            raise
    
    def check_alerts(self) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/api/datasources/proxy/uid/prometheus/api/v1/alerts"
            response = requests.get(url, auth=self.auth, verify=self.verify)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.error(f"Alert check failed: {e}")
            raise

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    try:
        client = ObservabilityClient()
        client.run_standard_test()
        _logger.info("Verification sequence complete")
    except Exception as e:
        _logger.error(f"Verification sequence failed: {e}")
        exit(1)
