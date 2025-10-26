# OpenTelemetry Integration Guide

This guide explains how to integrate OpenTelemetry into your LLM chatbot application and what happens when observability services are unavailable.

## 🚀 Quick Start

### 1. Install Dependencies

First, install the OpenTelemetry dependencies that were added to your `pyproject.toml`:

```bash
poetry install
```

The following packages are now included:
- `opentelemetry-api` - Core OpenTelemetry API
- `opentelemetry-sdk` - OpenTelemetry SDK implementation
- `opentelemetry-exporter-otlp` - OTLP exporter for sending data
- `opentelemetry-instrumentation` - Auto-instrumentation tools
- `opentelemetry-instrumentation-requests` - HTTP client instrumentation
- `opentelemetry-instrumentation-logging` - Logging instrumentation

### 2. Initialize Telemetry in Your Application

Add telemetry initialization to your application startup:

```python
from service.telemetry import initialize_telemetry

# Initialize telemetry (graceful degradation built-in)
success = initialize_telemetry(
    service_name="my-llm-service",
    service_version="1.0.0",
    environment="development",  # auto-detected from ENV var if not provided
    enable_tracing=True,
    enable_metrics=True,
    enable_logging=True,
    sampling_ratio=1.0  # 100% in development, use 0.1 in production
)
```

### 3. Use Telemetry in Your Code

```python
from service.telemetry import get_tracer, get_meter

# Get telemetry instances
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# In your LLM function
async def generate_response(prompt: str, user_id: str) -> str:
    # Create a span for this operation
    if tracer:
        with tracer.start_as_current_span(
            "llm.generate_response",
            attributes={
                "user.id": user_id,
                "prompt.length": len(prompt),
                "model": "gpt-3.5-turbo",
            }
        ) as span:
            # Your LLM logic here
            response = await call_llm_api(prompt)

            # Add events and metrics
            span.add_event("LLM API called", {"tokens_used": response.tokens})
            span.set_attribute("response.length", len(response.text))

            # Record metrics (if available)
            if meter:
                request_counter = meter.create_counter("llm_requests_total")
                request_counter.add(1, {"user.id": user_id, "status": "success"})

            return response.text
    else:
        # Fallback when tracing is not available
        response = await call_llm_api(prompt)
        return response.text
```

## 🔄 What Happens When Observability Services Are Down?

The telemetry system is designed with **graceful degradation** - your application continues to work normally even when observability services are unavailable.

### ✅ Application Behavior When Services Are Down

| Service | When Available | When Unavailable | Impact |
|---------|---------------|------------------|---------|
| **Jaeger (Traces)** | Full distributed tracing | Console logging only | ⚠️ No distributed traces, but app works |
| **Prometheus (Metrics)** | Rich metrics collection | Console metrics only | ⚠️ No metrics dashboards, but app works |
| **Loki (Logs)** | Structured log forwarding | Local logging only | ⚠️ No centralized logs, but app works |
| **OpenTelemetry Collector** | Data export to all services | Console fallback exporters | ⚠️ No data export, but app works |

### 🛡️ Graceful Degradation Features

1. **Automatic Service Detection**: The system automatically detects which services are available
2. **Fallback Exporters**: Console exporters are always used as backup
3. **No Application Crashes**: Your app never crashes due to telemetry issues
4. **Zero Data Loss**: All operations are logged locally even when services are down
5. **Automatic Recovery**: When services come back, full telemetry is restored

### 📊 Real-World Scenario Example

```python
# Scenario: Prometheus goes down during operation

# Before outage - full metrics
if meter:
    requests_counter.add(1, {"endpoint": "/generate", "status": "success"})

# During outage - graceful fallback
if meter:
    requests_counter.add(1, {"endpoint": "/generate", "status": "success"})
else:
    # Fallback logging when metrics unavailable
    logging.info("Request completed", extra={
        "endpoint": "/generate",
        "status": "success"
    })

# After outage - automatic recovery
# When Prometheus comes back, full metrics resume automatically
```

## 🎯 Complete Integration Example

Here's how to integrate telemetry into your AI proxy service:

### 1. Update Your Main Application

```python:service/ai-proxy-service/app/main.py
import logging
import sys
from fastapi import FastAPI

from .config import app_state
from .routes import GenerateRequest, generate_endpoint, health_endpoint, router
from .schema import schema
from .telemetry_middleware import (
    initialize_telemetry_for_service,
    shutdown_telemetry_for_service,
    create_instrumented_app,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create instrumented FastAPI app
app = create_instrumented_app(
    title="AI Proxy Service with OpenTelemetry",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    """Application startup with telemetry initialization"""
    logger.info("Starting AI Proxy Service...")

    # Load configuration
    app_state.load_config()
    await app_state.initialize_providers()

    # Initialize telemetry (handles service failures gracefully)
    await initialize_telemetry_for_service(
        service_name="ai-proxy-service",
        service_version="1.0.0"
    )

@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    await shutdown_telemetry_for_service()

# ... rest of your routes
```

### 2. Update Your Use Cases

```python:service/ai-proxy-service/core/usecases/generate_text.py
from ...telemetry import get_tracer, get_meter

tracer = get_tracer(__name__)
meter = get_meter(__name__)

async def generate_text(request: LLMRequest, provider: LLMProviderPort, ...) -> LLMResponse:
    """Generate text with comprehensive telemetry"""

    # Automatic tracing (if available)
    if tracer:
        with tracer.start_as_current_span(
            "llm.generate_text",
            attributes={
                "llm.provider": provider.__class__.__name__,
                "llm.model": getattr(request, 'model', 'unknown'),
                "user.id": getattr(request, 'user_id', 'anonymous'),
            }
        ) as span:
            return await _generate_with_telemetry(request, provider, ..., span)
    else:
        return await _generate_fallback(request, provider, ...)

async def _generate_with_telemetry(request, provider, ..., span):
    """Full telemetry implementation"""
    start_time = time.time()

    try:
        # Record request metrics
        if meter:
            counter = meter.create_counter("llm_requests_total")
            counter.add(1, {"status": "started"})

        # Make LLM call
        response = await provider.generate(...)

        # Record success metrics
        if meter:
            counter.add(1, {"status": "completed"})
            histogram = meter.create_histogram("llm_request_duration")
            histogram.record(time.time() - start_time)

        # Add span events
        span.add_event("LLM call completed", {
            "tokens_used": getattr(response, 'tokens', 0)
        })

        return response

    except Exception as e:
        # Record error metrics
        if meter:
            counter.add(1, {"status": "failed"})

        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
```

## 🔍 Monitoring Telemetry Status

### Check Telemetry Health

Add a health endpoint to monitor telemetry status:

```python
@app.get("/telemetry/status")
async def telemetry_status():
    """Get telemetry system status"""
    from service.telemetry import get_telemetry_manager

    manager = get_telemetry_manager()
    if manager:
        return {
            "telemetry_enabled": True,
            "service_name": manager.service_name,
            "tracing_enabled": manager.enable_tracing,
            "metrics_enabled": manager.enable_metrics,
            "logging_enabled": manager.enable_logging,
            "otlp_endpoint": manager.otlp_endpoint,
        }
    return {"telemetry_enabled": False}
```

### Application Startup Logs

When your application starts, you'll see logs like:

```
INFO - Starting AI Proxy Service...
INFO - Configuration loaded successfully
INFO - Initializing telemetry...
INFO - OTLP trace exporter configured
INFO - OTLP metrics exporter configured
INFO - Structured logging initialized
INFO - Telemetry initialized successfully
```

Or if services are down:

```
WARNING - OTLP trace exporter failed: Connection refused
WARNING - OTLP metrics exporter failed: Connection refused
INFO - Falling back to console exporters
INFO - Telemetry initialized with degraded functionality
```

## 📈 Production Considerations

### 1. Environment-Based Configuration

```python
import os

# Auto-configure based on environment
environment = os.getenv("ENVIRONMENT", "development")
sampling_ratio = 1.0 if environment == "development" else 0.1

initialize_telemetry(
    service_name="ai-proxy-service",
    environment=environment,
    sampling_ratio=sampling_ratio,
    enable_tracing=environment != "test",
    enable_metrics=True,
    enable_logging=True,
)
```

### 2. Resource Optimization

```python
# Adjust resource usage based on environment
if environment == "production":
    initialize_telemetry(
        # ... other params
        sampling_ratio=0.01,  # 1% sampling in production
        otlp_insecure=False,  # Use secure connections
    )
```

### 3. Service Dependencies

Your application **does not depend** on observability services:

- ✅ **Application starts successfully** even if Jaeger/Prometheus/Loki are down
- ✅ **All requests are processed** normally regardless of telemetry status
- ✅ **No performance impact** when services are unavailable
- ✅ **Automatic recovery** when services come back online

## 🧪 Testing Your Integration

### 1. Test with Services Running

```bash
# Start observability stack
cd infrastructure/orchestrator
python -m activities.common_activity.observability_stack_activity setup_complete_observability_stack

# Run your application
cd service/ai-proxy-service
python app/main_instrumented.py
```

### 2. Test with Services Down

```bash
# Stop observability services
docker stop prometheus loki jaeger otel-collector

# Run your application - it should work normally!
python app/main_instrumented.py

# Check telemetry status
curl http://localhost:8001/telemetry/status
```

### 3. Test Recovery

```bash
# Restart services
docker start prometheus loki jaeger otel-collector

# Check that telemetry automatically recovers
curl http://localhost:8001/telemetry/status
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Install dependencies
poetry install

# Or if using pip
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

#### 2. Connection Refused
```
WARNING - OTLP trace exporter failed: Connection refused
```
**This is normal!** The application continues working with console fallback.

#### 3. Port Conflicts
```
ERROR - Port 4317 already in use
```
Solution: Check what's using the port or modify port configuration.

#### 4. No Telemetry Data
- Check `/telemetry/status` endpoint
- Verify observability services are running
- Check application logs for telemetry initialization

### Debug Mode

Enable debug logging to see telemetry details:

```python
import logging
logging.getLogger("telemetry").setLevel(logging.DEBUG)
```

## 📚 Advanced Usage

### Custom Instrumentation

```python
from opentelemetry import trace

# Custom span with business logic
with tracer.start_as_current_span(
    "business_operation",
    attributes={
        "customer.id": customer_id,
        "operation.type": "purchase",
        "amount": 99.99,
    }
) as span:
    # Business logic
    result = process_purchase(customer_id, amount)

    if result.success:
        span.add_event("Purchase completed", {"order_id": result.order_id})
    else:
        span.set_status(Status(StatusCode.ERROR, result.error))
```

### Custom Metrics

```python
# Counter for business events
purchase_counter = meter.create_counter(
    "purchases_total",
    description="Total number of purchases"
)

# Histogram for response times
response_time = meter.create_histogram(
    "response_time_seconds",
    description="Response time in seconds"
)

# Use in code
purchase_counter.add(1, {"customer_tier": "premium"})
response_time.record(0.123, {"endpoint": "/api/purchase"})
```

## 🎉 Summary

**Your application is now fully instrumented with OpenTelemetry!**

✅ **Zero Downtime**: Works perfectly even when observability services are down  
✅ **Automatic Recovery**: Full telemetry restored when services come back  
✅ **Production Ready**: Configurable sampling, secure connections, resource optimization  
✅ **Comprehensive Coverage**: Traces, metrics, and logs with graceful fallbacks  
✅ **Developer Friendly**: Simple API with automatic service detection  

The telemetry system is designed to enhance observability without becoming a point of failure. Your LLM chatbot will continue to serve requests normally regardless of the observability infrastructure status! 🚀
