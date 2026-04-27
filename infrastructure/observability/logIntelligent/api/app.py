from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request

from infrastructure.observability.logIntelligent.api.schemas import (
    BatchIngestRequest,
    BatchIngestResponse,
    CapabilityMetricsResponse,
    IngestLogRequest,
    IngestLogResponse,
    LogLookupResponse,
    SimilarTemplatesResponse,
    TraceLookupResponse,
)
from infrastructure.observability.logIntelligent.api.service import LogIntelligenceService
from infrastructure.observability.logIntelligent.pipeline import LogIntelligencePipeline


def get_service(request: Request) -> LogIntelligenceService:
    return request.app.state.log_intelligence_service


def create_app(pipeline: LogIntelligencePipeline | None = None) -> FastAPI:
    app = FastAPI(title="Log Intelligent Architecture API", version="0.3.0")
    app.state.log_intelligence_service = LogIntelligenceService(pipeline or LogIntelligencePipeline())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/log-intelligence/metrics/capability", response_model=CapabilityMetricsResponse)
    def capability_metrics(service: LogIntelligenceService = Depends(get_service)) -> CapabilityMetricsResponse:
        return service.capability_metrics()

    @app.post("/api/v1/log-intelligence/ingest", response_model=IngestLogResponse)
    def ingest_log(
        payload: IngestLogRequest,
        service: LogIntelligenceService = Depends(get_service),
    ) -> IngestLogResponse:
        return service.ingest(payload)

    @app.post("/api/v1/log-intelligence/ingest/batch", response_model=BatchIngestResponse)
    def ingest_batch(
        payload: BatchIngestRequest,
        service: LogIntelligenceService = Depends(get_service),
    ) -> BatchIngestResponse:
        return BatchIngestResponse(items=service.ingest_batch(payload.logs))

    @app.get("/api/v1/log-intelligence/logs/{line_id}", response_model=LogLookupResponse)
    def lookup_log(line_id: str, service: LogIntelligenceService = Depends(get_service)) -> LogLookupResponse:
        return service.log_lookup(line_id)

    @app.get("/api/v1/log-intelligence/templates/{template_id}/similar", response_model=SimilarTemplatesResponse)
    def similar_templates(
        template_id: str,
        k: int = 5,
        service: LogIntelligenceService = Depends(get_service),
    ) -> SimilarTemplatesResponse:
        response = service.similar_templates(template_id, k=k)
        if not response.neighbors:
            raise HTTPException(status_code=404, detail="template_id not found")
        return response

    @app.get("/api/v1/log-intelligence/traces/{trace_id}", response_model=TraceLookupResponse)
    def trace_lookup(
        trace_id: str,
        service: LogIntelligenceService = Depends(get_service),
    ) -> TraceLookupResponse:
        return service.trace_lookup(trace_id)

    return app


app = create_app()
