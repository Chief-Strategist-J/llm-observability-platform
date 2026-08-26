from typing import Dict, Any, Optional
from opentelemetry.trace import Span

class GenAISemanticConventions:
    # System & Operation
    GEN_AI_SYSTEM = "gen_ai.system"
    GEN_AI_OPERATION_NAME = "gen_ai.operation.name"

    # Request Attributes
    GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
    GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
    GEN_AI_REQUEST_TOP_P = "gen_ai.request.top_p"
    GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
    GEN_AI_REQUEST_PRESENCE_PENALTY = "gen_ai.request.presence_penalty"
    GEN_AI_REQUEST_FREQUENCY_PENALTY = "gen_ai.request.frequency_penalty"

    # Response Attributes
    GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
    GEN_AI_RESPONSE_ID = "gen_ai.response.id"
    GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"

    # Usage Attributes
    GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

    # Server Attributes
    SERVER_ADDRESS = "server.address"
    SERVER_PORT = "server.port"

    @classmethod
    def apply_span_attributes(cls, span: Span, payload: Dict[str, Any]) -> None:
        if not span.is_recording():
            return

        provider = payload.get("provider", "unknown")
        span.set_attribute(cls.GEN_AI_SYSTEM, provider)
        span.set_attribute(cls.GEN_AI_OPERATION_NAME, payload.get("operation", "chat"))

        model = payload.get("model")
        if model:
            span.set_attribute(cls.GEN_AI_REQUEST_MODEL, str(model))
            span.set_attribute(cls.GEN_AI_RESPONSE_MODEL, str(model))

        if "prompt_tokens" in payload:
            span.set_attribute(cls.GEN_AI_USAGE_INPUT_TOKENS, int(payload["prompt_tokens"]))
        if "completion_tokens" in payload:
            span.set_attribute(cls.GEN_AI_USAGE_OUTPUT_TOKENS, int(payload["completion_tokens"]))

        if "finish_reason" in payload and payload["finish_reason"]:
            span.set_attribute(cls.GEN_AI_RESPONSE_FINISH_REASONS, [str(payload["finish_reason"])])

        if "temperature" in payload and payload["temperature"] is not None:
            span.set_attribute(cls.GEN_AI_REQUEST_TEMPERATURE, float(payload["temperature"]))
        if "top_p" in payload and payload["top_p"] is not None:
            span.set_attribute(cls.GEN_AI_REQUEST_TOP_P, float(payload["top_p"]))
        if "max_tokens" in payload and payload["max_tokens"] is not None:
            span.set_attribute(cls.GEN_AI_REQUEST_MAX_TOKENS, int(payload["max_tokens"]))
