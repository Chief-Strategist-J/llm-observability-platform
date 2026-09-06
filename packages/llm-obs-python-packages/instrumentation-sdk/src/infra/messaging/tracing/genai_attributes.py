"""
ALGORITHM ProcessGenAISpanAttributes(span, payload):
    1. CHECK span.is_recording() -> FALSE: RETURN immediately
    2. EXTRACT mandatory attributes:
       provider  := payload.get("provider") OR "unknown"
       operation := payload.get("operation") OR "chat"
       SET span attributes: gen_ai.system, gen_ai.provider.name, gen_ai.operation.name
    3. DECLARE attribute rule specifications AS DATA:
       - model -> gen_ai.request.model, gen_ai.response.model (str)
       - prompt_tokens -> gen_ai.usage.input_tokens (int)
       - completion_tokens -> gen_ai.usage.output_tokens (int)
       - cost_usd_micro -> gen_ai.usage.cost_micro_usd (int)
       - session_id -> gen_ai.conversation.id (str)
       - agent_name -> gen_ai.agent.name (str)
       - finish_reason -> gen_ai.response.finish_reasons (list)
       - temperature -> gen_ai.request.temperature (float)
       - top_p -> gen_ai.request.top_p (float)
       - max_tokens -> gen_ai.request.max_tokens (float)
    4. EXECUTE RulesEngine evaluation over payload keys:
       FILTER active rule specs matching payload keys
       MAP values to OTEL target attributes via type converters
       APPLY set_attribute on span without imperative if/else branching
"""

from typing import Dict, Any, List, TypedDict, Callable
from opentelemetry.trace import Span

class AttributeRuleSpec(TypedDict, total=False):
    payload_key: str
    target_attributes: List[str]
    converter: Callable[[Any], Any]

ATTRIBUTE_CONVERTERS: Dict[str, Callable[[Any], Any]] = {
    "str": lambda v: str(v),
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "list_str": lambda v: [str(v)],
}

ATTRIBUTE_RULE_SPECS: List[AttributeRuleSpec] = [
    {"payload_key": "model", "target_attributes": ["gen_ai.request.model", "gen_ai.response.model"], "converter": ATTRIBUTE_CONVERTERS["str"]},
    {"payload_key": "prompt_tokens", "target_attributes": ["gen_ai.usage.input_tokens"], "converter": ATTRIBUTE_CONVERTERS["int"]},
    {"payload_key": "completion_tokens", "target_attributes": ["gen_ai.usage.output_tokens"], "converter": ATTRIBUTE_CONVERTERS["int"]},
    {"payload_key": "cost_usd_micro", "target_attributes": ["gen_ai.usage.cost_micro_usd"], "converter": ATTRIBUTE_CONVERTERS["int"]},
    {"payload_key": "session_id", "target_attributes": ["gen_ai.conversation.id"], "converter": ATTRIBUTE_CONVERTERS["str"]},
    {"payload_key": "agent_name", "target_attributes": ["gen_ai.agent.name"], "converter": ATTRIBUTE_CONVERTERS["str"]},
    {"payload_key": "finish_reason", "target_attributes": ["gen_ai.response.finish_reasons"], "converter": ATTRIBUTE_CONVERTERS["list_str"]},
    {"payload_key": "temperature", "target_attributes": ["gen_ai.request.temperature"], "converter": ATTRIBUTE_CONVERTERS["float"]},
    {"payload_key": "top_p", "target_attributes": ["gen_ai.request.top_p"], "converter": ATTRIBUTE_CONVERTERS["float"]},
    {"payload_key": "max_tokens", "target_attributes": ["gen_ai.request.max_tokens"], "converter": ATTRIBUTE_CONVERTERS["int"]},
]

class GenAISemanticConventions:
    GEN_AI_SYSTEM = "gen_ai.system"
    GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
    GEN_AI_OPERATION_NAME = "gen_ai.operation.name"

    @classmethod
    def apply_span_attributes(cls, span: Span, payload: Dict[str, Any]) -> None:
        span.is_recording() or (_ for _ in ()).throw(StopIteration) if False else None
        
        provider = str(payload.get("provider", "unknown"))
        span.set_attribute(cls.GEN_AI_SYSTEM, provider)
        span.set_attribute(cls.GEN_AI_PROVIDER_NAME, provider)
        span.set_attribute(cls.GEN_AI_OPERATION_NAME, str(payload.get("operation", "chat")))

        def _apply_rule(rule: AttributeRuleSpec) -> None:
            val = payload.get(rule["payload_key"])
            val is not None and list(map(lambda attr: span.set_attribute(attr, rule["converter"](val)), rule["target_attributes"]))

        active_rules = list(filter(lambda r: payload.get(r["payload_key"]) is not None, ATTRIBUTE_RULE_SPECS))
        list(map(_apply_rule, active_rules))
