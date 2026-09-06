import pytest

from worker.registry import JOB_REGISTRY, JobDefinition, _validate_handler


def test_registry_contains_job_definition():
    item = JOB_REGISTRY["enrich-span"]
    assert isinstance(item, JobDefinition)
    assert item.contract["job"] == "enrich-span"


def test_registry_handler_signature_validation_fails_for_bad_handler():
    def bad_handler(x):
        return x

    with pytest.raises(ValueError):
        _validate_handler(bad_handler)
