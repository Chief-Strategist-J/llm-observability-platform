from __future__ import annotations

from pydantic import BaseModel, Field


class IngestLogRequest(BaseModel):
    line_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class IngestLogResponse(BaseModel):
    line_id: str
    template_id: str
    template_text: str
    normalized_fields: dict[str, str]
    anomaly_score: float
    storage_tier: str


class BatchIngestRequest(BaseModel):
    logs: list[IngestLogRequest]


class BatchIngestResponse(BaseModel):
    items: list[IngestLogResponse]


class SimilarTemplatesResponse(BaseModel):
    template_id: str
    neighbors: list[str]


class TraceLookupResponse(BaseModel):
    trace_id: str
    line_ids: list[str]


class LogLookupResponse(BaseModel):
    found: bool
    item: IngestLogResponse | None = None


class CapabilityMetricsResponse(BaseModel):
    implemented: list[str]
    partial: list[str]
    pending: list[str]
    readiness_score: float
