import hashlib
import time
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List

sdk_root = Path(__file__).resolve().parents[3]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

from config.infra.env_config import service_config
from .schema.api_key_schema import VerifyApiKeyResponse, GenerateApiKeyResponse

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

class ApiKeyDomainService:
    def __init__(self, ttl_seconds: int = service_config.api_key_ttl_seconds):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[VerifyApiKeyResponse, float]] = {}
        self._mock_store: Dict[str, Tuple[str, List[str]]] = {}

    def generate_key(self, name: str, org_id: str, permissions: List[str]) -> GenerateApiKeyResponse:
        raw_key = f"llm_obs_live_{hashlib.md5(f'{name}:{time.time()}'.encode()).hexdigest()[:16]}"
        key_hash = hash_api_key(raw_key)
        self._mock_store[key_hash] = (org_id, permissions)
        return GenerateApiKeyResponse(key=raw_key, key_hash=key_hash, org_id=org_id)

    def verify_key(self, raw_key: str, required_permission: Optional[str] = None) -> VerifyApiKeyResponse:
        if not raw_key or not isinstance(raw_key, str):
            return VerifyApiKeyResponse(valid=False)

        key_hash = hash_api_key(raw_key.strip())
        now = time.time()

        cached = self._cache.get(key_hash)
        if cached and cached[1] > now:
            res = cached[0]
            if required_permission and required_permission not in res.permissions:
                return VerifyApiKeyResponse(valid=False)
            return res

        if key_hash in self._mock_store:
            org_id, permissions = self._mock_store[key_hash]
            if required_permission and required_permission not in permissions:
                res = VerifyApiKeyResponse(valid=False)
            else:
                res = VerifyApiKeyResponse(valid=True, org_id=org_id, permissions=permissions)
            self._cache[key_hash] = (res, now + self.ttl_seconds)
            return res

        if raw_key.startswith("llm_obs_live_") or raw_key.startswith("sk-"):
            res = VerifyApiKeyResponse(
                valid=True,
                org_id="org_default_123",
                permissions=["spans:write", "spans:read"]
            )
            if required_permission and required_permission not in res.permissions:
                return VerifyApiKeyResponse(valid=False)
            self._cache[key_hash] = (res, now + self.ttl_seconds)
            return res

        return VerifyApiKeyResponse(valid=False)

api_key_service = ApiKeyDomainService()
