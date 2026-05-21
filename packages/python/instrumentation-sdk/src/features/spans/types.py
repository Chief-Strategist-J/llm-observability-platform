import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

class FinishReason(str, Enum):
    UNSPECIFIED = "unspecified"
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    TIMEOUT = "timeout"
    TOOL_CALLS = "tool_calls"
    CACHE_HIT = "cache_hit"
    CLIENT_DISCONNECT = "client_disconnect"

class TokenCountMethod(str, Enum):
    UNSPECIFIED = "unspecified"
    TIKTOKEN = "tiktoken"
    ESTIMATED = "estimated"

class Environment(str, Enum):
    UNSPECIFIED = "unspecified"
    PRODUCTION = "production"
    STAGING = "staging"
    DEV = "dev"

class LLMSpan(BaseModel):
    model_config = ConfigDict(frozen=True)

    span_id: uuid.UUID
    trace_id: Optional[uuid.UUID] = None
    parent_span_id: Optional[uuid.UUID] = None
    schema_version: Literal[1] = 1
    model: str = Field(min_length=1)
    provider: str
    service_name: str = Field(min_length=1)
    endpoint: str
    environment: Environment = Environment.UNSPECIFIED
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt_tokens: int = Field(gt=0)
    completion_tokens: int = Field(ge=0)
    latency_ms_ttft: Optional[int] = None
    latency_ms_total: int = Field(gt=0)
    finish_reason: FinishReason
    cost_usd_micro: int = Field(ge=0)
    price_version: str
    token_count_method: TokenCountMethod = TokenCountMethod.UNSPECIFIED
    is_sampled: bool = False
    retry_count: int = Field(0, ge=0)
    attempted_models: List[str] = Field(default_factory=list)
    pii_detected: bool = False
    injection_attempt: bool = False
    timestamp_utc: datetime
    
    # Sampled-only fields
    prompt_hash: Optional[str] = Field(None, min_length=64, max_length=64)
    prompt_embedding: Optional[List[float]] = Field(None, min_length=384, max_length=384)
    response_embedding: Optional[List[float]] = Field(None, min_length=384, max_length=384)

    # Warning field (not part of the input, but part of the output after validation)
    span_warnings: List[str] = Field(default_factory=list, exclude=True)

    @field_validator("finish_reason", "token_count_method", "environment", mode="before")
    @classmethod
    def normalize_proto_enums(cls, v: Any) -> Any:
        if isinstance(v, str) and "_" in v:
            # Maps "FINISH_REASON_STOP" -> "stop"
            return v.split("_")[-1].lower()
        return v

    @field_validator("timestamp_utc")
    @classmethod
    def validate_timestamp_bounds(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        if v > now + timedelta(seconds=60):
            raise ValueError("RULE-V-09: timestamp_utc is > 60 seconds in the future")
        if v < now - timedelta(days=7):
            raise ValueError("RULE-V-10: timestamp_utc is > 7 days in the past")
        return v

    @model_validator(mode="after")
    def validate_sampled_fields(self) -> "LLMSpan":
        if self.pii_detected or not self.is_sampled:
            if self.prompt_hash is not None or self.prompt_embedding is not None or self.response_embedding is not None:
                object.__setattr__(self, "prompt_hash", None)
                object.__setattr__(self, "prompt_embedding", None)
                object.__setattr__(self, "response_embedding", None)
        return self

    @model_validator(mode="after")
    def apply_warning_rules(self) -> "LLMSpan":
        warnings = list(self.span_warnings)

        # RULE-W-01: token_count_method == 'estimated'
        if self.token_count_method == TokenCountMethod.ESTIMATED:
            warnings.append("RULE-W-01: token_count_method == 'estimated' -> warn: cost accuracy reduced")

        # RULE-W-02: retry_count > 0
        if self.retry_count > 0:
            warnings.append("RULE-W-02: retry_count > 0 -> warn: latency includes retry overhead")

        # RULE-W-03: latency_ms_ttft > latency_ms_total
        if self.latency_ms_ttft is not None and self.latency_ms_ttft > self.latency_ms_total:
            warnings.append("RULE-W-03: latency_ms_ttft > latency_ms_total -> warn: clock inconsistency, ttft set to null")
            object.__setattr__(self, "latency_ms_ttft", None)

        # RULE-W-04: completion_tokens == 0 AND finish_reason == 'stop'
        if self.completion_tokens == 0 and self.finish_reason == FinishReason.STOP:
            warnings.append("RULE-W-04: completion_tokens == 0 AND finish_reason == 'stop' -> warn: empty response")

        # RULE-W-05: attempted_models has > 1 entry
        if self.attempted_models and len(self.attempted_models) > 1:
            warnings.append("RULE-W-05: attempted_models has > 1 entry -> warn: fallback chain occurred")

        object.__setattr__(self, "span_warnings", warnings)
        return self
