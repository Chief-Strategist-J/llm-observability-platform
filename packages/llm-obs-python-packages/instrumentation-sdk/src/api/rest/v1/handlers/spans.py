from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Dict
from pydantic import ValidationError
from .....features.spans.types import LLMSpan
from .....features.spans.globals import get_reporter

router = APIRouter(tags=["Ingestion"])

@router.post("/spans", status_code=202)
def record_span(span_data: Dict[str, Any]) -> JSONResponse:
    trace_id = span_data.get("trace_id")
    if trace_id:
        from .....features.spans.fallback_tracker import track_fallback
        from .....features.spans.tool_call_tracker import track_tool_call
        retry_count, attempted_models = track_fallback(trace_id, span_data.get("model"))
        span_data["attempted_models"] = attempted_models
        span_data["retry_count"] = max(span_data.get("retry_count", 0), retry_count)
        track_tool_call(trace_id, span_data.get("span_id"), span_data.get("cost_usd_micro", 0))
    elif span_data.get("model") and not span_data.get("attempted_models"):
        span_data["attempted_models"] = [span_data.get("model")]

    try:
        span = LLMSpan(**span_data)
    except ValidationError as e:
        err_detail = e.errors()[0]
        msg = err_detail["msg"]
        loc = err_detail["loc"]
        field = str(loc[-1]) if loc else ""
        if "RULE-V-09" in msg:
            rule = "RULE-V-09"
        elif "RULE-V-10" in msg:
            rule = "RULE-V-10"
        elif field == "prompt_tokens":
            rule = "RULE-V-02"
        elif field == "latency_ms_total":
            rule = "RULE-V-03"
        elif field == "completion_tokens":
            rule = "RULE-V-04"
        elif field == "cost_usd_micro":
            rule = "RULE-V-05"
        elif field == "service_name":
            rule = "RULE-V-06"
        elif field == "model":
            rule = "RULE-V-07"
        elif field == "span_id":
            rule = "RULE-V-01"
        else:
            rule = "RULE-V-99"
        clean_msg = msg
        if "RULE-V-" in msg and ":" in msg:
            clean_msg = msg.split(":", 1)[1].strip()
        return JSONResponse(
            status_code=400,
            content={"error": f"Validation failed for field '{field}': {clean_msg}", "rule": rule}
        )
    
    reporter = get_reporter()
    reporter.report(span.model_dump(mode="json"))
    return JSONResponse(
        status_code=202,
        content={"success": True, "span_warnings": span.span_warnings}
    )
