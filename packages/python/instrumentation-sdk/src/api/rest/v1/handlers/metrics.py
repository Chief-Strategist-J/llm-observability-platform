from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from opentelemetry import trace
from src.features.metrics.index import record_span_metrics, init_metrics_pipeline, get_current_prices_ref, reload_prices, record_forecast_metrics


class ModelPriceResponse(BaseModel):
    model: str
    provider: str
    input_price_per_1m: float
    output_price_per_1m: float
    version: str


class ModelPricesListResponse(BaseModel):
    prices: List[ModelPriceResponse]


class RecordForecastRequest(BaseModel):
    mean: int
    p10: int
    p90: int
    model: str = "unknown"
    provider: str = "unknown"
    service_name: str = "unknown"


router = APIRouter(prefix="/metrics", tags=["Metrics"])


class MetricsStatusResponse(BaseModel):
    initialized: bool
    message: str


class MetricsInitRequest(BaseModel):
    port: Optional[int] = None


class RecordSpanMetricsRequest(BaseModel):
    model: str = "unknown"
    provider: str = "unknown"
    service_name: str = "unknown"
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost_usd_micro: Optional[int] = None
    latency_ms_total: Optional[int] = None
    latency_ms_ttft: Optional[int] = None
    finish_reason: Optional[str] = None
    status: str = "success"
    pii_detected: bool = False
    injection_attempt: bool = False
    retry_count: int = 0


class RecordSpanMetricsResponse(BaseModel):
    recorded: bool
    cost_usd_micro: Optional[int] = None
    price_version: Optional[str] = None


class BatchRecordRequest(BaseModel):
    spans: List[RecordSpanMetricsRequest]


class BatchRecordResponse(BaseModel):
    recorded_count: int


def _set_span_attributes() -> None:
    span = trace.get_current_span()
    span.set_attribute("service.name", "instrumentation-sdk-api")
    span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
    span.set_attribute("feature.name", "metrics")


@router.post("/init", response_model=MetricsStatusResponse)
def init_metrics(request: MetricsInitRequest = MetricsInitRequest()):
    _set_span_attributes()
    try:
        init_metrics_pipeline(request.port)
        return MetricsStatusResponse(initialized=True, message="Metrics pipeline initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=MetricsStatusResponse)
def metrics_health():
    _set_span_attributes()
    from prometheus_client import generate_latest
    from src.features.metrics.index import _initialized
    metrics_data = generate_latest().decode('utf-8')
    return MetricsStatusResponse(
        initialized=_initialized,
        message=metrics_data,
    )


@router.post("/record", response_model=RecordSpanMetricsResponse)
def record_metrics(request: RecordSpanMetricsRequest):
    _set_span_attributes()
    try:
        span_data = request.model_dump(exclude_none=True)
        record_span_metrics(span_data)
        return RecordSpanMetricsResponse(
            recorded=True,
            cost_usd_micro=span_data.get("cost_usd_micro"),
            price_version=span_data.get("price_version"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-batch", response_model=BatchRecordResponse)
def record_batch(request: BatchRecordRequest):
    _set_span_attributes()
    count = 0
    for span_req in request.spans:
        try:
            span_data = span_req.model_dump(exclude_none=True)
            record_span_metrics(span_data)
            count += 1
        except Exception:
            pass
    return BatchRecordResponse(recorded_count=count)


@router.get("/prices", response_model=ModelPricesListResponse)
def get_prices():
    _set_span_attributes()
    prices = get_current_prices_ref()
    return ModelPricesListResponse(
        prices=[
            ModelPriceResponse(
                model=p.get("model", ""),
                provider=p.get("provider", ""),
                input_price_per_1m=float(p.get("input_price_per_1m", 0.0)),
                output_price_per_1m=float(p.get("output_price_per_1m", 0.0)),
                version=p.get("version", ""),
            )
            for p in prices
        ]
    )


@router.post("/prices/reload", response_model=MetricsStatusResponse)
def reload_model_prices():
    _set_span_attributes()
    try:
        reload_prices()
        from src.features.metrics.index import _initialized
        return MetricsStatusResponse(
            initialized=_initialized,
            message="Model prices reloaded successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast", response_model=MetricsStatusResponse)
def record_forecast(request: RecordForecastRequest):
    _set_span_attributes()
    try:
        labels = {
            "model": request.model,
            "provider": request.provider,
            "service_name": request.service_name,
        }
        record_forecast_metrics(request.mean, request.p10, request.p90, labels)
        from src.features.metrics.index import _initialized
        return MetricsStatusResponse(
            initialized=_initialized,
            message="Forecast metrics recorded successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

