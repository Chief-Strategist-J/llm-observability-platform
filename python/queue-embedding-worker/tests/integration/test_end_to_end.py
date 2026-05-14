from api.index import execute


def test_e2e_enrich_span_output_shape():
    payload = {"trace_id": "t1", "span_id": "s1", "text": "abc", "model": "text-embedding-3-small"}
    out = execute("enrich-span", payload, env={"EMBEDDING_DIMENSIONS": "256"})
    result = out["result"]
    assert set(result.keys()) == {"trace_id", "span_id", "embedding_key", "dimensions", "model", "provider"}


def test_e2e_enrich_span_key_prefix():
    payload = {"trace_id": "t2", "span_id": "s2", "text": "abc", "model": "text-embedding-3-small"}
    out = execute("enrich-span", payload, env={"EMBEDDING_DIMENSIONS": "256"})
    assert out["result"]["embedding_key"].startswith("emb_")
