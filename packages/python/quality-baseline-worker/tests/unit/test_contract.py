from shared.contracts.validator import load_workflow_contracts

def test_load_workflow_contracts() -> None:
    res = load_workflow_contracts()
    assert "recompute" in res
    assert "rollup" in res
    assert res["recompute"]["workflow"] == "recompute_quality_baseline"
    assert res["rollup"]["workflow"] == "rollup_quality_trend"
