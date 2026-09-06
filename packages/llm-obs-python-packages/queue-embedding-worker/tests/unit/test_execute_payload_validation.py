import pytest

from api.index import execute


@pytest.mark.parametrize(
    "payload",
    [
        {"span_id": "s", "text": "x", "model": "m"},
        {"trace_id": "t", "text": "x", "model": "m"},
        {"trace_id": "t", "span_id": "s", "model": "m"},
        {"trace_id": "t", "span_id": "s", "text": "x"},
    ],
)
def test_execute_requires_all_fields(payload):
    with pytest.raises(TypeError):
        execute("enrich-span", payload, env={"EMBEDDING_DIMENSIONS": "8"})


def test_execute_rejects_non_integer_dimensions():
    payload = {"trace_id": "t", "span_id": "s", "text": "x", "model": "m"}
    with pytest.raises(Exception):
        execute("enrich-span", payload, env={"EMBEDDING_DIMENSIONS": "abc"})
