import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient
from infrastructure.messaging.setup.inngest.inngest_activity import (
    start_inngest_activity,
    stop_inngest_activity,
    restart_inngest_activity,
    delete_inngest_activity,
    get_inngest_status_activity,
)


class ServiceRequest(BaseModel):
    instance_id: int = 0
    env_vars: Optional[Dict[str, str]] = None
    force: bool = True


class BatchServiceRequest(BaseModel):
    instance_ids: List[int]
    env_vars: Optional[Dict[str, str]] = None
    force: bool = True


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


def get_container_status(instance_id: int = 0) -> dict:
    container_name = f"inngest-instance-{instance_id}"
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}|{{.Status}}|{{.State}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|")
            if len(parts) >= 3:
                return {"service": "inngest", "instance_id": instance_id, "name": parts[0], "status": parts[1], "state": parts[2], "is_running": parts[2] == "running"}
    except Exception as e:
        return {"service": "inngest", "instance_id": instance_id, "error": str(e)}
    return {"service": "inngest", "instance_id": instance_id, "is_running": False, "state": "not_found"}


app = FastAPI(title="Inngest Service API")
ws_manager = ConnectionManager()
obs = ObservabilityClient(service_name="inngest-service-api")


@app.post("/start")
async def start_service(request: ServiceRequest = None):
    req = request or ServiceRequest()
    obs.log_info(f"api_start_inngest instance_id={req.instance_id}")
    await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": "starting"})

    try:
        params = {"instance_id": req.instance_id, "env_vars": req.env_vars or {}}
        result = await start_inngest_activity(params)
        status = "running" if result.get("success") else "failed"
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": status, "result": result})
        await ws_manager.broadcast({"event": "operation_complete", "service": "inngest", "instance_id": req.instance_id, "success": result.get("success")})
        obs.log_info(f"api_start_inngest_complete instance_id={req.instance_id} success={result.get('success')}")
        return result
    except Exception as e:
        obs.log_error(f"api_start_inngest_failed instance_id={req.instance_id} error={e}")
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": "error", "error": str(e)})
        return {"success": False, "service": "inngest", "instance_id": req.instance_id, "error": str(e)}


@app.post("/stop")
async def stop_service(request: ServiceRequest = None):
    req = request or ServiceRequest()
    obs.log_info(f"api_stop_inngest instance_id={req.instance_id}")
    await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": "stopping"})

    try:
        params = {"instance_id": req.instance_id, "force": req.force, "env_vars": req.env_vars or {}}
        result = await stop_inngest_activity(params)
        status = "stopped" if result.get("success") else "failed"
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": status, "result": result})
        await ws_manager.broadcast({"event": "operation_complete", "service": "inngest", "instance_id": req.instance_id, "success": result.get("success")})
        obs.log_info(f"api_stop_inngest_complete instance_id={req.instance_id} success={result.get('success')}")
        return result
    except Exception as e:
        obs.log_error(f"api_stop_inngest_failed instance_id={req.instance_id} error={e}")
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": req.instance_id, "status": "error", "error": str(e)})
        return {"success": False, "service": "inngest", "instance_id": req.instance_id, "error": str(e)}


@app.get("/status")
async def status(instance_id: int = 0):
    obs.log_info(f"api_inngest_status instance_id={instance_id}")
    try:
        result = await get_inngest_status_activity({"instance_id": instance_id})
        await ws_manager.broadcast({"event": "status_check", "service": "inngest", "instance_id": instance_id, "is_running": result.get("is_running")})
        return result
    except Exception as e:
        fallback = get_container_status(instance_id)
        await ws_manager.broadcast({"event": "status_check", "service": "inngest", "instance_id": instance_id, "is_running": fallback.get("is_running")})
        return fallback


@app.post("/start-batch")
async def start_batch(request: BatchServiceRequest):
    obs.log_info(f"api_start_inngest_batch instance_ids={request.instance_ids}")
    results = {}
    for iid in request.instance_ids:
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": "starting"})
        try:
            params = {"instance_id": iid, "env_vars": request.env_vars or {}}
            result = await start_inngest_activity(params)
            results[str(iid)] = result
            status = "running" if result.get("success") else "failed"
            await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": status})
        except Exception as e:
            results[str(iid)] = {"success": False, "error": str(e)}
            await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": "error", "error": str(e)})
    obs.log_info(f"api_start_inngest_batch_complete count={len(request.instance_ids)}")
    return {"success": True, "results": results}


@app.post("/stop-batch")
async def stop_batch(request: BatchServiceRequest):
    obs.log_info(f"api_stop_inngest_batch instance_ids={request.instance_ids}")
    results = {}
    for iid in request.instance_ids:
        await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": "stopping"})
        try:
            params = {"instance_id": iid, "force": request.force, "env_vars": request.env_vars or {}}
            result = await stop_inngest_activity(params)
            results[str(iid)] = result
            status = "stopped" if result.get("success") else "failed"
            await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": status})
        except Exception as e:
            results[str(iid)] = {"success": False, "error": str(e)}
            await ws_manager.broadcast({"event": "status_update", "service": "inngest", "instance_id": iid, "status": "error", "error": str(e)})
    obs.log_info(f"api_stop_inngest_batch_complete count={len(request.instance_ids)}")
    return {"success": True, "results": results}


@app.get("/services")
async def list_services():
    obs.log_info("api_inngest_list_services")
    instances = []
    for iid in range(5):
        info = get_container_status(iid)
        if info.get("is_running") or info.get("state") != "not_found":
            instances.append(info)
    return {"service": "inngest", "instances": instances, "count": len(instances)}


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await ws_manager.connect(websocket)
    obs.log_info("ws_inngest_client_connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "get_status":
                    iid = msg.get("instance_id", 0)
                    result = get_container_status(iid)
                    await websocket.send_json({"event": "status_response", **result, "timestamp": datetime.now(timezone.utc).isoformat()})
                elif msg.get("action") == "ping":
                    await websocket.send_json({"event": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "message": "invalid_json", "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        obs.log_info("ws_inngest_client_disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8202)
