from contracts.validator import load_event_contract

def test_contract_validator():
    res = load_event_contract()
    assert res["event"] == "llm_spans_raw"
    assert res["version"] == 1
    assert res["consumer_group"] == "latency-engine-cg"
