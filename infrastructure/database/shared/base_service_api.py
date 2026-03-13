import sys
import time
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient
from infrastructure.database.shared.database_definitions import DATABASE_CONFIG, DatabaseService


class ServiceRequest(BaseModel):
    env_vars: Optional[Dict[str, str]] = None


class BatchServiceRequest(BaseModel):
    services: List[str]
    env_vars: Optional[Dict[str, str]] = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


def get_container_status(service_name: str) -> dict:
    containers = []
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={service_name}", "--format", "{{.Names}}|{{.Status}}|{{.State}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 3:
                    containers.append({
                        "name": parts[0],
                        "status": parts[1],
                        "state": parts[2]
                    })
    except Exception as e:
        return {"service": service_name, "containers": [], "error": str(e)}

    is_running = any(c["state"] == "running" for c in containers)
    return {
        "service": service_name,
        "is_running": is_running,
        "containers": containers
    }


def create_database_service_app(
    service_name: str,
    setup_fn: Callable,
    teardown_fn: Callable,
    available_services: Optional[List[str]] = None
) -> FastAPI:
    app = FastAPI(title=f"{service_name.capitalize()} Service API")
    ws_manager = ConnectionManager()
    obs = ObservabilityClient(service_name=f"{service_name}-service-api")

    if available_services is None:
        available_services = [s.value for s in DatabaseService]

    @app.post("/start")
    async def start_service(request: ServiceRequest = None):
        obs.log_info(f"api_start_service_begin service={service_name}")
        await ws_manager.broadcast({"event": "status_update", "service": service_name, "status": "starting"})

        try:
            params = {"env_vars": request.env_vars if request and request.env_vars else {}}
            result = await setup_fn(params)

            event = "status_update"
            status = "running" if result.get("success") else "failed"
            await ws_manager.broadcast({"event": event, "service": service_name, "status": status, "result": result})
            await ws_manager.broadcast({"event": "operation_complete", "service": service_name, "success": result.get("success"), "duration_ms": result.get("duration_ms", 0)})

            obs.log_info(f"api_start_service_complete service={service_name} success={result.get('success')}")
            return result
        except Exception as e:
            obs.log_error(f"api_start_service_failed service={service_name} error={e}")
            await ws_manager.broadcast({"event": "status_update", "service": service_name, "status": "error", "error": str(e)})
            return {"success": False, "service": service_name, "error": str(e)}

    @app.post("/stop")
    async def stop_service(request: ServiceRequest = None):
        obs.log_info(f"api_stop_service_begin service={service_name}")
        await ws_manager.broadcast({"event": "status_update", "service": service_name, "status": "stopping"})

        try:
            params = {"env_vars": request.env_vars if request and request.env_vars else {}}
            result = await teardown_fn(params)

            status = "stopped" if result.get("success") else "failed"
            await ws_manager.broadcast({"event": "status_update", "service": service_name, "status": status, "result": result})
            await ws_manager.broadcast({"event": "operation_complete", "service": service_name, "success": result.get("success"), "duration_ms": result.get("duration_ms", 0)})

            obs.log_info(f"api_stop_service_complete service={service_name} success={result.get('success')}")
            return result
        except Exception as e:
            obs.log_error(f"api_stop_service_failed service={service_name} error={e}")
            await ws_manager.broadcast({"event": "status_update", "service": service_name, "status": "error", "error": str(e)})
            return {"success": False, "service": service_name, "error": str(e)}

    @app.get("/status")
    async def status():
        obs.log_info(f"api_get_status service={service_name}")
        result = get_container_status(service_name)
        await ws_manager.broadcast({"event": "status_check", "service": service_name, "is_running": result.get("is_running")})
        return result

    @app.post("/start-batch")
    async def start_batch(request: BatchServiceRequest):
        obs.log_info(f"api_start_batch services={request.services}")
        results = {}
        for svc in request.services:
            await ws_manager.broadcast({"event": "status_update", "service": svc, "status": "starting"})
            try:
                params = {"env_vars": request.env_vars or {}}
                result = await setup_fn(params)
                results[svc] = result
                status = "running" if result.get("success") else "failed"
                await ws_manager.broadcast({"event": "status_update", "service": svc, "status": status})
            except Exception as e:
                results[svc] = {"success": False, "error": str(e)}
                await ws_manager.broadcast({"event": "status_update", "service": svc, "status": "error", "error": str(e)})

        obs.log_info(f"api_start_batch_complete count={len(request.services)}")
        return {"success": True, "results": results}

    @app.post("/stop-batch")
    async def stop_batch(request: BatchServiceRequest):
        obs.log_info(f"api_stop_batch services={request.services}")
        results = {}
        for svc in request.services:
            await ws_manager.broadcast({"event": "status_update", "service": svc, "status": "stopping"})
            try:
                params = {"env_vars": request.env_vars or {}}
                result = await teardown_fn(params)
                results[svc] = result
                status = "stopped" if result.get("success") else "failed"
                await ws_manager.broadcast({"event": "status_update", "service": svc, "status": status})
            except Exception as e:
                results[svc] = {"success": False, "error": str(e)}
                await ws_manager.broadcast({"event": "status_update", "service": svc, "status": "error", "error": str(e)})

        obs.log_info(f"api_stop_batch_complete count={len(request.services)}")
        return {"success": True, "results": results}

    @app.get("/services")
    async def list_services():
        obs.log_info("api_list_services")
        services = []
        for svc_name in available_services:
            status_info = get_container_status(svc_name)
            services.append({
                "name": svc_name,
                "is_running": status_info.get("is_running", False),
                "containers": status_info.get("containers", []),
                "config": DATABASE_CONFIG.get(svc_name, {})
            })
        return {"services": services, "count": len(services)}

    @app.websocket("/ws/status")
    async def websocket_status(websocket: WebSocket):
        await ws_manager.connect(websocket)
        obs.log_info(f"ws_client_connected service={service_name}")
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("action") == "get_status":
                        target = msg.get("service", service_name)
                        result = get_container_status(target)
                        await websocket.send_json({"event": "status_response", **result, "timestamp": datetime.now(timezone.utc).isoformat()})
                    elif msg.get("action") == "ping":
                        await websocket.send_json({"event": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                except json.JSONDecodeError:
                    await websocket.send_json({"event": "error", "message": "invalid_json", "timestamp": datetime.now(timezone.utc).isoformat()})
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
            obs.log_info(f"ws_client_disconnected service={service_name}")

    return app
