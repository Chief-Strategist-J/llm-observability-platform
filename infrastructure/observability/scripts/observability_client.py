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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("ObservabilityClient")

class ObservabilityClient:
    def __init__(self, endpoint: str = "http://172.28.0.10:4317", service_name: str = "observability-client"):
        self.endpoint = endpoint
        self.service_name = service_name
        self.resource = Resource.create({"service.name": service_name})
        self.gauge_value = 0
        
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

    def gauge_callback(self, options: object) -> Iterable[Observation]:
        yield Observation(self.gauge_value)

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
            self.meter.create_observable_gauge(
                "test_gauge",
                callbacks=[self.gauge_callback],
                description="Gauge for testing alerts"
            )
        except Exception as e:
            _logger.error(f"Error setting up metrics: {e}")
            raise

    def log_info(self, msg: str, attributes: Optional[Dict] = None):
        try:
            self.logger.info(msg, extra=attributes)
        except Exception as e:
            _logger.error(f"Failed to send info log: {e}")

    def log_error(self, msg: str, attributes: Optional[Dict] = None):
        try:
            self.logger.error(msg, extra=attributes)
        except Exception as e:
            _logger.error(f"Failed to send error log: {e}")

    def increment_counter(self, amount: int = 1, attributes: Optional[Dict] = None):
        try:
            self.counter.add(amount, attributes or {})
        except Exception as e:
            _logger.error(f"Failed to increment counter: {e}")

    def trigger_test_alert(self, value: int = 10, duration_sec: int = 30):
        try:
            _logger.info(f"Triggering alert with value {value} for {duration_sec}s")
            self.gauge_value = value
            start = time.time()
            while time.time() - start < duration_sec:
                time.sleep(1)
                self.increment_counter(1)
            self.gauge_value = 0
            _logger.info("Alert trigger completed")
        except Exception as e:
            _logger.error(f"Error triggering alert: {e}")
            self.gauge_value = 0

    def run_standard_test(self):
        try:
            _logger.info("Running standard verification test")
            with self.tracer.start_as_current_span("standard_test") as span:
                span.set_attribute("test.id", "standard-run")
                self.log_info("Standard test running", {"status": "active"})
                self.increment_counter(1, {"action": "test"})
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
        verifier = ObservabilityVerifier()

        client.run_standard_test()
        
        _logger.info("Starting Alert Trigger Sequence...")
        client.trigger_test_alert(value=15, duration_sec=60)
        
        _logger.info("Validating Metrics...")
        metrics = verifier.query_prometheus("test_counter_total")
        
        _logger.info("Validating Logs...")
        logs = verifier.query_loki('{job="observability-client"}')

        _logger.info("Validating Traces...")
        traces = verifier.query_traces("observability-client")
        
        _logger.info("Validating Alerts...")
        alerts = verifier.check_alerts()
        
        _logger.info("All verifications passed successfully")
        
    except Exception as e:
        _logger.error(f"Verification sequence failed: {e}")
        exit(1)
