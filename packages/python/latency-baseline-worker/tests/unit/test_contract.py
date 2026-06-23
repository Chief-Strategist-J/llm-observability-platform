from shared.contracts.validator import load_workflow_contracts

def test_load_workflow_contracts() -> None:
    contracts = load_workflow_contracts()
    assert "latency_baseline" in contracts
    assert contracts["latency_baseline"]["workflow"] == "LatencyBaselineWorkflow"
    assert contracts["latency_baseline"]["cron"] == "5 * * * *"
