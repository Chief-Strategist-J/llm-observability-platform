from dataclasses import FrozenInstanceError
import pytest

from shared.types.job import JobEnvelope
from worker.registry import JOB_REGISTRY
from jobs.enrich_span.types import EnrichSpanPayload, EnrichSpanResult


def test_registry_has_expected_single_job():
    assert set(JOB_REGISTRY.keys()) == {"enrich-span"}


def test_job_envelope_dataclass_works():
    env = JobEnvelope(job_name="enrich-span", payload={"x": 1})
    assert env.job_name == "enrich-span"


def test_payload_dataclass_is_frozen():
    payload = EnrichSpanPayload("t", "s", "x", "m")
    with pytest.raises(FrozenInstanceError):
        payload.text = "changed"


def test_result_dataclass_is_frozen():
    result = EnrichSpanResult("t", "s", "emb_123", 1, "m")
    with pytest.raises(FrozenInstanceError):
        result.model = "changed"
