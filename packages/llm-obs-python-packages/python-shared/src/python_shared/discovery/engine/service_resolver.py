import os
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
import httpx

from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.discovery.catalog.service_catalog import DEFAULT_SERVICE_CATALOG, resolve_service_endpoint
from python_shared.discovery.models.service_models import ServiceInstanceModel, ResolveServiceData

logger = logging.getLogger("python_shared.discovery.engine")

class ServiceResolverOptions:
    def __init__(
        self,
        registry_url: Optional[str] = None,
        secret: Optional[str] = None,
        ttl_seconds: float = HTTP_CONSTANTS.DEFAULT_RESOLVER_TTL_MS / 1000.0,
        timeout_seconds: float = HTTP_CONSTANTS.DEFAULT_RESOLVER_TIMEOUT_MS / 1000.0,
    ):
        self.registry_url = (
            registry_url
            or os.getenv(HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_URL)
            or os.getenv("SERVICE_DISCOVERY_URL")
            or HTTP_CONSTANTS.DEFAULT_SERVICE_REGISTRY_URL
        )
        self.secret = (
            secret
            or os.getenv(HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_SECRET)
            or os.getenv(HTTP_CONSTANTS.ENV_SERVICE_REGISTRY_TOKEN)
        )
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds

class ServiceResolver:
    def __init__(self, options: Optional[ServiceResolverOptions] = None):
        self.options = options or ServiceResolverOptions()
        self._cache: Dict[str, Tuple[str, List[ServiceInstanceModel], float]] = {}
        self._lock = threading.RLock()

    @property
    def registry_url(self) -> str:
        return self.options.registry_url.rstrip("/")

    def _build_headers(self) -> Dict[str, str]:
        headers = {HTTP_CONSTANTS.HEADER_ACCEPT: HTTP_CONSTANTS.CONTENT_TYPE_JSON}
        if self.options.secret:
            headers[HTTP_CONSTANTS.HEADER_AUTHORIZATION] = f"{HTTP_CONSTANTS.BEARER_PREFIX}{self.options.secret}"
        return headers

    def _is_cache_fresh(self, cached_at: float) -> bool:
        return (time.time() - cached_at) < self.options.ttl_seconds

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def resolve_sync(self, service_name: str, fallback_url: Optional[str] = None) -> str:
        with self._lock:
            if service_name in self._cache:
                endpoint, _, cached_at = self._cache[service_name]
                if self._is_cache_fresh(cached_at):
                    return endpoint

        remote_data = self._fetch_remote_sync(service_name)
        if remote_data and remote_data.endpoint:
            with self._lock:
                self._cache[service_name] = (remote_data.endpoint, remote_data.instances, time.time())
            return remote_data.endpoint

        return resolve_service_endpoint(service_name, fallback_url)

    def resolve_all_sync(self, service_name: str) -> List[ServiceInstanceModel]:
        with self._lock:
            if service_name in self._cache:
                _, instances, cached_at = self._cache[service_name]
                if self._is_cache_fresh(cached_at):
                    return instances

        remote_data = self._fetch_remote_sync(service_name)
        if remote_data and remote_data.instances:
            with self._lock:
                self._cache[service_name] = (remote_data.endpoint, remote_data.instances, time.time())
            return remote_data.instances

        return []

    def _fetch_remote_sync(self, service_name: str) -> Optional[ResolveServiceData]:
        url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_RESOLVE}"
        params = {HTTP_CONSTANTS.PARAM_SERVICE: service_name}
        headers = self._build_headers()

        try:
            with httpx.Client(timeout=self.options.timeout_seconds) as client:
                res = client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    json_data = res.json()
                    if json_data.get("success") and json_data.get("data"):
                        return ResolveServiceData.model_validate(json_data["data"])
        except Exception as e:
            logger.warning(f"[ServiceResolver] Failed remote resolve '{service_name}': {e}")
        return None

    async def resolve(self, service_name: str, fallback_url: Optional[str] = None) -> str:
        with self._lock:
            if service_name in self._cache:
                endpoint, _, cached_at = self._cache[service_name]
                if self._is_cache_fresh(cached_at):
                    return endpoint

        remote_data = await self._fetch_remote_async(service_name)
        if remote_data and remote_data.endpoint:
            with self._lock:
                self._cache[service_name] = (remote_data.endpoint, remote_data.instances, time.time())
            return remote_data.endpoint

        return resolve_service_endpoint(service_name, fallback_url)

    async def resolve_all(self, service_name: str) -> List[ServiceInstanceModel]:
        with self._lock:
            if service_name in self._cache:
                _, instances, cached_at = self._cache[service_name]
                if self._is_cache_fresh(cached_at):
                    return instances

        remote_data = await self._fetch_remote_async(service_name)
        if remote_data and remote_data.instances:
            with self._lock:
                self._cache[service_name] = (remote_data.endpoint, remote_data.instances, time.time())
            return remote_data.instances

        return []

    async def _fetch_remote_async(self, service_name: str) -> Optional[ResolveServiceData]:
        url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_RESOLVE}"
        params = {HTTP_CONSTANTS.PARAM_SERVICE: service_name}
        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=self.options.timeout_seconds) as client:
                res = await client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    json_data = res.json()
                    if json_data.get("success") and json_data.get("data"):
                        return ResolveServiceData.model_validate(json_data["data"])
        except Exception as e:
            logger.warning(f"[ServiceResolver] Async resolve failed '{service_name}': {e}")
        return None

service_resolver = ServiceResolver()

def resolve_service_url_sync(service_name: str, fallback_url: Optional[str] = None) -> str:
    return service_resolver.resolve_sync(service_name, fallback_url)

async def resolve_service_url(service_name: str, fallback_url: Optional[str] = None) -> str:
    return await service_resolver.resolve(service_name, fallback_url)
