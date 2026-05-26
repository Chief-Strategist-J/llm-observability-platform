import pytest
from shared.contracts.validator import (
    load_workflow_contract,
    validate_workflow_contract,
)
from shared.errors.base import ValidationError


def test_load_workflow_contract() -> None:
    contract = load_workflow_contract()
    assert contract["workflow"] == "ewma_baseline_update"
    assert contract["version"] == 1
    assert contract["cron"] == "0 * * * *"


def test_validate_workflow_contract_invalid() -> None:
    with pytest.raises(ValidationError):
        validate_workflow_contract("invalid_text")
