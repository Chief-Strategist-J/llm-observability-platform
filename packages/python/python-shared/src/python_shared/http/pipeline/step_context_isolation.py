import json
from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.http.pipeline.types import PipelineContext

def calculate_payload_size_bytes(body: any) -> int:
    if body is None:
        return 0
    if isinstance(body, (bytes, bytearray)):
        return len(body)
    if isinstance(body, str):
        return len(body.encode("utf-8"))
    try:
        return len(json.dumps(body).encode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid request payload: unable to serialize body ({e})")

class StepContextIsolation:
    name: str = "ContextIsolation"
    description: str = "Request Context Isolation & Payload Size Guard"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        headers = dict(ctx.config.headers or {})

        ctx.tenantId = headers.get(HTTP_CONSTANTS.HEADER_X_TENANT_ID, HTTP_CONSTANTS.DEFAULT_TENANT_ID)
        headers[HTTP_CONSTANTS.HEADER_X_TENANT_ID] = ctx.tenantId
        ctx.config.headers = headers

        body_size_bytes = calculate_payload_size_bytes(ctx.config.body)
        max_body_bytes = ctx.config.max_body_size_bytes or 10485760

        if body_size_bytes > max_body_bytes:
            raise ValueError(f"Request payload size ({body_size_bytes} bytes) exceeds maximum limit of {max_body_bytes} bytes")
