"""In-process API surface for health and dry-run job execution."""

from worker.config import load_config
from worker.index import handle_job
from shared.tracing.tracer import worker_span


def health(env: dict[str, str] | None = None) -> dict:
    with worker_span("api.health", feature_name="worker-health"):
        cfg = load_config(env)
        return {
            "status": "ok",
            "queue": cfg.queue_name,
            "concurrency": cfg.concurrency,
            "rate_limit_per_sec": cfg.rate_limit_per_sec,
        }


def execute(job_name: str, payload: dict, *, env: dict[str, str] | None = None) -> dict:
    with worker_span("api.execute", feature_name=job_name):
        return {
            "status": "processed",
            "job": job_name,
            "result": handle_job(job_name, payload, env=env),
        }
