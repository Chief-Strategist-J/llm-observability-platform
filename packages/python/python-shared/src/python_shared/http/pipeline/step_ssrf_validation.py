from urllib.parse import urlparse
from python_shared.http.pipeline.types import PipelineContext

class StepSsrfValidation:
    name: str = "SsrfValidation"
    description: str = "SSRF Destination & IP Allowlist Guard"

    async def execute(self, ctx: PipelineContext) -> None:
        ctx.step_index += 1
        parsed = urlparse(ctx.config.url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL for SSRF validation: {ctx.config.url}")
        if ctx.config.allowed_hosts and parsed.hostname not in ctx.config.allowed_hosts:
            raise ValueError(f"Target host '{parsed.hostname}' is not in allowed hosts list")
