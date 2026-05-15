"""Cloudflare queue worker entrypoint."""

from worker.config import load_config
from worker.registry import JOB_REGISTRY
from shared.tracing.tracer import worker_span


def handle_job(job_name: str, message: dict, *, env: dict[str, str] | None = None) -> dict:
    config = load_config(env)
    with worker_span("queue.consume", feature_name=job_name):
        try:
            job = JOB_REGISTRY[job_name]
        except KeyError as exc:
            raise KeyError(f"Unknown job '{job_name}'") from exc
        return job.handler(message, dimensions=config.embedding_dimensions, provider_name=config.embedding_provider)
