import pytest

from api.index import execute, health


def _payload(text="hello"):
    return {
        "trace_id": "t1",
        "span_id": "s1",
        "text": text,
        "model": "text-embedding-3-small",
    }


def test_health_ok():
    out = health({})
    assert out["status"] == "ok"


def test_health_includes_controls():
    out = health({"WORKER_CONCURRENCY": "9", "WORKER_RATE_LIMIT_PER_SEC": "99"})
    assert out["concurrency"] == 9
    assert out["rate_limit_per_sec"] == 99


def test_execute_success():
    out = execute("enrich-span", _payload(), env={"EMBEDDING_DIMENSIONS": "128"})
    assert out["status"] == "processed"
    assert out["result"]["dimensions"] == 128


@pytest.mark.parametrize("job_name", ["bad", "unknown", "", "ENRICH-SPAN"]) 
def test_execute_unknown_job(job_name):
    with pytest.raises(KeyError):
        execute(job_name, _payload(), env={})


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_execute_invalid_text(text):
    with pytest.raises(Exception):
        execute("enrich-span", _payload(text), env={})
