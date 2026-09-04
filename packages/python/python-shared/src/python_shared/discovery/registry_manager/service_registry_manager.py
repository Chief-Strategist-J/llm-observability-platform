import os
import time
import signal
import atexit
import logging
import asyncio
import threading
from typing import Dict, Optional, Any
import httpx

from python_shared.http.constants import HTTP_CONSTANTS
from python_shared.discovery.catalog.service_catalog import SERVICE_CATALOG_META
from python_shared.discovery.models.service_models import (
    RegisterInstanceRequest,
    HeartbeatInstanceRequest,
    DeregisterInstanceRequest,
    HealthCheckSpec,
)

logger = logging.getLogger("python_shared.discovery.registry_manager")

class ServiceRegistryManagerOptions:
    def __init__(
        self,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        version: Optional[str] = None,
        weight: int = 100,
        metadata: Optional[Dict[str, str]] = None,
        health_path: Optional[str] = None,
        registry_url: Optional[str] = None,
        secret: Optional[str] = None,
        heartbeat_interval_seconds: float = HTTP_CONSTANTS.DEFAULT_HEARTBEAT_INTERVAL_MS / 1000.0,
        timeout_seconds: float = 3.0,
    ):
        self.name = name if name is not None else (os.getenv(HTTP_CONSTANTS.ENV_SERVICE_NAME) or os.getenv("APP_NAME") or "python-service")
        self.host = host if host is not None else (os.getenv(HTTP_CONSTANTS.ENV_HOST) or os.getenv("SERVICE_HOST") or HTTP_CONSTANTS.HOST_LOCALHOST)

        catalog_meta = SERVICE_CATALOG_META.get(self.name, {})
        default_port = catalog_meta.get("defaultPort", 8000)
        env_port = os.getenv(HTTP_CONSTANTS.ENV_PORT) or os.getenv("SERVICE_PORT")
        self.port = port if port is not None else (int(env_port) if env_port else default_port)

        self.protocol = protocol or catalog_meta.get("protocol", HTTP_CONSTANTS.PROTOCOL_HTTP)
        self.version = version or os.getenv("APP_VERSION", "1.0.0")
        self.weight = weight
        self.metadata = metadata or {}
        self.health_path = health_path or catalog_meta.get("healthPath", HTTP_CONSTANTS.ENDPOINT_HEALTH)

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
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.timeout_seconds = timeout_seconds

class ServiceRegistryManager:
    def __init__(self, options: Optional[ServiceRegistryManagerOptions] = None):
        self.options = options or ServiceRegistryManagerOptions()
        self.instance_id: Optional[str] = None
        self._is_registered = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_stop_event = threading.Event()
        self._async_heartbeat_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        self._shutdown_hook_registered = False

    @property
    def registry_url(self) -> str:
        return self.options.registry_url.rstrip("/")

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            HTTP_CONSTANTS.HEADER_CONTENT_TYPE: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
            HTTP_CONSTANTS.HEADER_ACCEPT: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
        }
        if self.options.secret:
            headers[HTTP_CONSTANTS.HEADER_AUTHORIZATION] = f"{HTTP_CONSTANTS.BEARER_PREFIX}{self.options.secret}"
        return headers

    def register_sync(self) -> Optional[str]:
        with self._lock:
            url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_REGISTER}"
            payload = RegisterInstanceRequest(
                name=self.options.name,
                host=self.options.host,
                port=self.options.port,
                protocol=self.options.protocol,
                version=self.options.version,
                weight=self.options.weight,
                metadata=self.options.metadata,
                health_check=HealthCheckSpec(
                    protocol=self.options.protocol,
                    path=self.options.health_path,
                ),
            ).model_dump(by_alias=True)

            try:
                with httpx.Client(timeout=self.options.timeout_seconds) as client:
                    res = client.post(url, json=payload, headers=self._build_headers())
                    if res.status_code in (200, 201):
                        data = res.json()
                        if data.get("success") and data.get("data", {}).get("id"):
                            self.instance_id = data["data"]["id"]
                            self._is_registered = True
                            self.start_heartbeat_sync()
                            self._attach_shutdown_hooks()
                            return self.instance_id
            except Exception as e:
                logger.error(f"[ServiceRegistry] Exception registering '{self.options.name}': {e}")
            return None

    def send_heartbeat_sync(self) -> bool:
        if not self.instance_id:
            return False

        url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_HEARTBEAT}"
        payload = HeartbeatInstanceRequest(
            name=self.options.name,
            instance_id=self.instance_id,
        ).model_dump(by_alias=True)

        try:
            with httpx.Client(timeout=self.options.timeout_seconds) as client:
                res = client.post(url, json=payload, headers=self._build_headers())
                if res.status_code == 200 and res.json().get("success"):
                    return True
        except Exception as e:
            logger.warning(f"[ServiceRegistry] Heartbeat failed '{self.options.name}': {e}")
        return False

    def deregister_sync(self) -> bool:
        with self._lock:
            self.stop_heartbeat_sync()
            if not self.instance_id:
                return True

            url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_DEREGISTER}"
            payload = DeregisterInstanceRequest(
                name=self.options.name,
                instance_id=self.instance_id,
            ).model_dump(by_alias=True)

            try:
                with httpx.Client(timeout=self.options.timeout_seconds) as client:
                    res = client.post(url, json=payload, headers=self._build_headers())
                    if res.status_code == 200:
                        self.instance_id = None
                        self._is_registered = False
                        return True
            except Exception as e:
                logger.error(f"[ServiceRegistry] Exception deregistering '{self.options.name}': {e}")

            self.instance_id = None
            self._is_registered = False
            return False

    def start_heartbeat_sync(self) -> None:
        self.stop_heartbeat_sync()
        self._heartbeat_stop_event.clear()

        def _loop():
            while not self._heartbeat_stop_event.is_set():
                time.sleep(self.options.heartbeat_interval_seconds)
                if self._heartbeat_stop_event.is_set():
                    break
                self.send_heartbeat_sync()

        self._heartbeat_thread = threading.Thread(target=_loop, daemon=True, name=f"heartbeat-{self.options.name}")
        self._heartbeat_thread.start()

    def stop_heartbeat_sync(self) -> None:
        self._heartbeat_stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)
        self._heartbeat_thread = None

    async def register(self) -> Optional[str]:
        with self._lock:
            url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_REGISTER}"
            payload = RegisterInstanceRequest(
                name=self.options.name,
                host=self.options.host,
                port=self.options.port,
                protocol=self.options.protocol,
                version=self.options.version,
                weight=self.options.weight,
                metadata=self.options.metadata,
                health_check=HealthCheckSpec(
                    protocol=self.options.protocol,
                    path=self.options.health_path,
                ),
            ).model_dump(by_alias=True)

            try:
                async with httpx.AsyncClient(timeout=self.options.timeout_seconds) as client:
                    res = await client.post(url, json=payload, headers=self._build_headers())
                    if res.status_code in (200, 201):
                        data = res.json()
                        if data.get("success") and data.get("data", {}).get("id"):
                            self.instance_id = data["data"]["id"]
                            self._is_registered = True
                            self.start_heartbeat_async()
                            self._attach_shutdown_hooks()
                            return self.instance_id
            except Exception as e:
                logger.error(f"[ServiceRegistry] Async exception registering '{self.options.name}': {e}")
            return None

    async def send_heartbeat(self) -> bool:
        if not self.instance_id:
            return False

        url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_HEARTBEAT}"
        payload = HeartbeatInstanceRequest(
            name=self.options.name,
            instance_id=self.instance_id,
        ).model_dump(by_alias=True)

        try:
            async with httpx.AsyncClient(timeout=self.options.timeout_seconds) as client:
                res = await client.post(url, json=payload, headers=self._build_headers())
                if res.status_code == 200 and res.json().get("success"):
                    return True
        except Exception as e:
            logger.warning(f"[ServiceRegistry] Async heartbeat failed '{self.options.name}': {e}")
        return False

    async def deregister(self) -> bool:
        with self._lock:
            await self.stop_heartbeat_async()
            if not self.instance_id:
                return True

            url = f"{self.registry_url}{HTTP_CONSTANTS.ENDPOINT_DEREGISTER}"
            payload = DeregisterInstanceRequest(
                name=self.options.name,
                instance_id=self.instance_id,
            ).model_dump(by_alias=True)

            try:
                async with httpx.AsyncClient(timeout=self.options.timeout_seconds) as client:
                    res = await client.post(url, json=payload, headers=self._build_headers())
                    if res.status_code == 200:
                        self.instance_id = None
                        self._is_registered = False
                        return True
            except Exception as e:
                logger.error(f"[ServiceRegistry] Async exception deregistering '{self.options.name}': {e}")

            self.instance_id = None
            self._is_registered = False
            return False

    def start_heartbeat_async(self) -> None:
        self.stop_heartbeat_sync()

        async def _loop():
            while self._is_registered and self.instance_id:
                await asyncio.sleep(self.options.heartbeat_interval_seconds)
                await self.send_heartbeat()

        try:
            loop = asyncio.get_running_loop()
            self._async_heartbeat_task = loop.create_task(_loop())
        except RuntimeError:
            self.start_heartbeat_sync()

    async def stop_heartbeat_async(self) -> None:
        if self._async_heartbeat_task and not self._async_heartbeat_task.done():
            self._async_heartbeat_task.cancel()
            try:
                await self._async_heartbeat_task
            except asyncio.CancelledError:
                pass
        self._async_heartbeat_task = None
        self.stop_heartbeat_sync()

    def _attach_shutdown_hooks(self) -> None:
        with self._lock:
            if self._shutdown_hook_registered:
                return
            self._shutdown_hook_registered = True

            def _on_shutdown():
                if self.instance_id:
                    self.deregister_sync()

            atexit.register(_on_shutdown)

            try:
                for sig in (signal.SIGINT, signal.SIGTERM):
                    prev_handler = signal.getsignal(sig)
                    def _sig_handler(signum, frame, old_h=prev_handler):
                        _on_shutdown()
                        if callable(old_h) and old_h not in (signal.SIG_IGN, signal.SIG_DFL):
                            old_h(signum, frame)
                    signal.signal(sig, _sig_handler)
            except (ValueError, TypeError):
                pass

service_registry_manager = ServiceRegistryManager()

def register_fastapi_service(
    app: Any,
    service_name: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    registry_url: Optional[str] = None,
    manager: Optional[ServiceRegistryManager] = None,
) -> ServiceRegistryManager:
    options = ServiceRegistryManagerOptions(
        name=service_name,
        host=host,
        port=port,
        registry_url=registry_url,
    )
    mgr = manager or ServiceRegistryManager(options)

    @app.on_event("startup")
    async def _on_startup():
        await mgr.register()

    @app.on_event("shutdown")
    async def _on_shutdown():
        await mgr.deregister()

    return mgr
