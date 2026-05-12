"""OpenTelemetry metrics adapter implementing MetricsPort."""

from typing import Dict, Any, Optional
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

from kafka_messaging_internal.shared.errors.exceptions import map_adapter_error, SystemError
from kafka_messaging_internal.shared.ports.metrics_port import MetricsPort


class OTELMetricsAdapter(MetricsPort):
    """OpenTelemetry implementation of MetricsPort with tracing."""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.service_name = config.get('OTEL_SERVICE_NAME', 'kafka-messaging-internal')
        self.service_version = config.get('OTEL_SERVICE_VERSION', '1.0.0')
        self.deployment_env = config.get('DEPLOYMENT_ENV', 'development')
        self.host_name = config.get('HOST_NAME', 'localhost')
        self.otlp_endpoint = config.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
        
        try:
            # Initialize OpenTelemetry metrics
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "deployment.env": self.deployment_env,
                "host.name": self.host_name
            })
            
            exporter = OTLPMetricExporter(endpoint=self.otlp_endpoint)
            self.meter_provider = MeterProvider(resource=resource, metric_exporters=[exporter])
            metrics.set_meter_provider(self.meter_provider)
            
            self.meter = metrics.get_meter(__name__)
            
            # Create common metrics
            self.event_counter = self.meter.create_counter(
                "events_processed_total",
                description="Total number of events processed"
            )
            
            self.event_duration = self.meter.create_histogram(
                "event_processing_duration_seconds",
                description="Duration of event processing in seconds"
            )
            
            self.error_counter = self.meter.create_counter(
                "errors_total",
                description="Total number of errors"
            )
            
            self.active_connections = self.meter.create_up_down_counter(
                "active_connections",
                description="Number of active connections"
            )
            
            self.queue_size = self.meter.create_up_down_counter(
                "queue_size",
                description="Current queue size"
            )
            
        except Exception as e:
            error = map_adapter_error('system', 'configuration_error', e)
            raise error
    
    def increment_counter(self, metric_name: str, value: float = 1.0, attributes: Optional[Dict[str, Any]] = None):
        """Increment a counter metric."""
        try:
            attrs = attributes or {}
            
            if metric_name == "events_processed_total":
                self.event_counter.add(value, attrs)
            elif metric_name == "errors_total":
                self.error_counter.add(value, attrs)
            else:
                # Create dynamic counter
                counter = self.meter.create_counter(metric_name)
                counter.add(value, attrs)
                
        except Exception as e:
            error = map_adapter_error('system', 'internal_error', e)
            raise error
    
    def record_histogram(self, metric_name: str, value: float, attributes: Optional[Dict[str, Any]] = None):
        """Record a histogram metric."""
        try:
            attrs = attributes or {}
            
            if metric_name == "event_processing_duration_seconds":
                self.event_duration.record(value, attrs)
            else:
                # Create dynamic histogram
                histogram = self.meter.create_histogram(metric_name)
                histogram.record(value, attrs)
                
        except Exception as e:
            error = map_adapter_error('system', 'internal_error', e)
            raise error
    
    def set_gauge(self, metric_name: str, value: float, attributes: Optional[Dict[str, Any]] = None):
        """Set a gauge metric value."""
        try:
            attrs = attributes or {}
            
            if metric_name == "active_connections":
                # UpDownCounter can be used as gauge by setting delta
                current_value = self.active_connections._instrument._value
                delta = value - current_value
                self.active_connections.add(delta, attrs)
            elif metric_name == "queue_size":
                current_value = self.queue_size._instrument._value
                delta = value - current_value
                self.queue_size.add(delta, attrs)
            else:
                # Create dynamic gauge using up-down counter
                gauge = self.meter.create_up_down_counter(metric_name)
                # Note: This is a simplified approach
                # In practice, you might want to use ObservableGauge
                gauge.add(value, attrs)
                
        except Exception as e:
            error = map_adapter_error('system', 'internal_error', e)
            raise error
    
    def increment_events_processed(self, event_type: str, status: str = "success"):
        """Increment events processed counter with attributes."""
        self.increment_counter(
            "events_processed_total",
            attributes={
                "event_type": event_type,
                "status": status,
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )
    
    def increment_errors(self, error_type: str, component: str):
        """Increment errors counter with attributes."""
        self.increment_counter(
            "errors_total",
            attributes={
                "error_type": error_type,
                "component": component,
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )
    
    def record_event_duration(self, duration_seconds: float, event_type: str):
        """Record event processing duration."""
        self.record_histogram(
            "event_processing_duration_seconds",
            duration_seconds,
            attributes={
                "event_type": event_type,
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )
    
    def set_active_connections(self, count: int, connection_type: str):
        """Set active connections gauge."""
        self.set_gauge(
            "active_connections",
            float(count),
            attributes={
                "connection_type": connection_type,
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )
    
    def set_queue_size(self, size: int, queue_name: str):
        """Set queue size gauge."""
        self.set_gauge(
            "queue_size",
            float(size),
            attributes={
                "queue_name": queue_name,
                "service.name": self.service_name,
                "service.version": self.service_version
            }
        )
    
    def create_timer(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a timer for measuring duration."""
        attrs = attributes or {}
        
        class Timer:
            def __init__(self, adapter, metric_name, metric_attrs):
                self.adapter = adapter
                self.metric_name = metric_name
                self.metric_attrs = metric_attrs
                self.start_time = None
            
            def __enter__(self):
                import time
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time is not None:
                    import time
                    duration = time.time() - self.start_time
                    self.adapter.record_histogram(self.metric_name, duration, self.metric_attrs)
        
        return Timer(self, name, attrs)
    
    def flush(self):
        """Flush metrics (if applicable)."""
        # OTLP exporter handles flushing automatically
        pass
