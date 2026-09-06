import pytest

from shared.contracts.validator import ContractValidationError, load_enrich_span_contract, validate_enrich_span_contract


def test_load_contract_valid():
    contract = load_enrich_span_contract()
    assert contract["job"] == "enrich-span"


def test_validate_contract_missing_key_fails():
    with pytest.raises(ContractValidationError):
        validate_enrich_span_contract("job: enrich-span")


def test_validate_contract_invalid_pattern_fails():
    invalid_text = """
job: enrich-span
version: 2
queue: span-enrichment
timeout_seconds: 30
retry:
  max_attempts: 5
  backoff_ms: 500
payload:
  required: [trace_id, span_id, model, text]
result:
  pattern: 'emb_.*'
"""
    with pytest.raises(ContractValidationError):
        validate_enrich_span_contract(invalid_text)
