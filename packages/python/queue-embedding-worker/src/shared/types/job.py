from dataclasses import dataclass


@dataclass(frozen=True)
class JobEnvelope:
    job_name: str
    payload: dict
