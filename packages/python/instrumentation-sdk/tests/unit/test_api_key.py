import pytest
from src.features.api_keys.service import ApiKeyDomainService, hash_api_key

def test_api_key_hashing():
    raw_key = "llm_obs_live_testkey123"
    hashed = hash_api_key(raw_key)
    assert isinstance(hashed, str)
    assert len(hashed) == 64

def test_api_key_generation_and_verification():
    service = ApiKeyDomainService()
    generated = service.generate_key(name="test-key", org_id="org_test_123", permissions=["spans:write"])

    assert generated.key.startswith("llm_obs_live_")
    assert generated.org_id == "org_test_123"

    res_valid = service.verify_key(generated.key, required_permission="spans:write")
    assert res_valid.valid is True
    assert res_valid.org_id == "org_test_123"

    res_invalid_perm = service.verify_key(generated.key, required_permission="admin:delete")
    assert res_invalid_perm.valid is False

def test_invalid_api_key_verification():
    service = ApiKeyDomainService()
    res = service.verify_key("invalid_random_string")
    assert res.valid is False
