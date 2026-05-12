"""Inngest service API handlers following OpenAPI contract."""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel, Field

from application.activities.inngest_activity import start_inngest_activity, stop_inngest_activity

logger = logging.getLogger(__name__)


class ServiceRequest(BaseModel):
    """Request model for service operations"""
    instance_id: int = Field(0, description="Instance ID")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    force: bool = Field(True, description="Force operation")


class BatchServiceRequest(BaseModel):
    """Request model for batch service operations"""
    instances: List[int] = Field(..., description="List of instance IDs")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    force: bool = Field(True, description="Force operation")


class ServiceStatus(BaseModel):
    """Response model for service status"""
    instance_id: int = Field(..., description="Instance ID")
    status: str = Field(..., description="Service status")
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    last_updated: datetime = Field(..., description="Last updated timestamp")


class ServiceResponse(BaseModel):
    """Response model for service operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")
    instance_id: int = Field(..., description="Instance ID")
    timestamp: datetime = Field(..., description="Operation timestamp")


class InngestServiceAPI:
    """REST API handlers for Inngest service operations"""
    
    def __init__(self):
        self.router = FastAPI()
        self._setup_routes()
        self._active_connections: List[WebSocket] = []
        self._service_status: Dict[int, ServiceStatus] = {}

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/start", response_model=ServiceResponse)
        async def start_service(request: ServiceRequest) -> ServiceResponse:
            """Start Inngest service"""
            try:
                result = await start_inngest_activity({
                    "instance_id": request.instance_id,
                    "env_vars": request.env_vars,
                    "force": request.force
                })
                
                if result.get("success"):
                    self._service_status[request.instance_id] = ServiceStatus(
                        instance_id=request.instance_id,
                        status="running",
                        uptime=0,
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    # Notify WebSocket clients
                    await self._notify_status_change(request.instance_id, "running")
                
                return ServiceResponse(
                    success=result.get("success", False),
                    message=result.get("message", "Service started"),
                    instance_id=request.instance_id,
                    timestamp=datetime.now(timezone.utc)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/stop", response_model=ServiceResponse)
        async def stop_service(request: ServiceRequest) -> ServiceResponse:
            """Stop Inngest service"""
            try:
                result = await stop_inngest_activity({
                    "instance_id": request.instance_id,
                    "force": request.force
                })
                
                if result.get("success"):
                    self._service_status[request.instance_id] = ServiceStatus(
                        instance_id=request.instance_id,
                        status="stopped",
                        uptime=None,
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    # Notify WebSocket clients
                    await self._notify_status_change(request.instance_id, "stopped")
                
                return ServiceResponse(
                    success=result.get("success", False),
                    message=result.get("message", "Service stopped"),
                    instance_id=request.instance_id,
                    timestamp=datetime.now(timezone.utc)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/restart", response_model=ServiceResponse)
        async def restart_service(request: ServiceRequest) -> ServiceResponse:
            """Restart Inngest service"""
            try:
                # Stop first
                await stop_inngest_activity({
                    "instance_id": request.instance_id,
                    "force": request.force
                })
                
                # Then start
                result = await start_inngest_activity({
                    "instance_id": request.instance_id,
                    "env_vars": request.env_vars,
                    "force": request.force
                })
                
                if result.get("success"):
                    self._service_status[request.instance_id] = ServiceStatus(
                        instance_id=request.instance_id,
                        status="running",
                        uptime=0,
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    # Notify WebSocket clients
                    await self._notify_status_change(request.instance_id, "running")
                
                return ServiceResponse(
                    success=result.get("success", False),
                    message=result.get("message", "Service restarted"),
                    instance_id=request.instance_id,
                    timestamp=datetime.now(timezone.utc)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/start/batch", response_model=List[ServiceResponse])
        async def start_batch(request: BatchServiceRequest) -> List[ServiceResponse]:
            """Start multiple instances"""
            responses = []
            for instance_id in request.instances:
                try:
                    result = await start_inngest_activity({
                        "instance_id": instance_id,
                        "env_vars": request.env_vars,
                        "force": request.force
                    })
                    
                    if result.get("success"):
                        self._service_status[instance_id] = ServiceStatus(
                            instance_id=instance_id,
                            status="running",
                            uptime=0,
                            last_updated=datetime.now(timezone.utc)
                        )
                        
                        # Notify WebSocket clients
                        await self._notify_status_change(instance_id, "running")
                    
                    responses.append(ServiceResponse(
                        success=result.get("success", False),
                        message=result.get("message", "Service started"),
                        instance_id=instance_id,
                        timestamp=datetime.now(timezone.utc)
                    ))
                except Exception as e:
                    responses.append(ServiceResponse(
                        success=False,
                        message=str(e),
                        instance_id=instance_id,
                        timestamp=datetime.now(timezone.utc)
                    ))
            
            return responses

        @self.router.get("/status", response_model=List[ServiceStatus])
        async def get_status() -> List[ServiceStatus]:
            """Get status of all instances"""
            return list(self._service_status.values())

        @self.router.get("/status/{instance_id}", response_model=ServiceStatus)
        async def get_instance_status(instance_id: int) -> ServiceStatus:
            """Get status of specific instance"""
            if instance_id not in self._service_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Instance {instance_id} not found"
                )
            
            return self._service_status[instance_id]

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time status updates"""
            await websocket.accept()
            self._active_connections.append(websocket)
            
            try:
                # Send current status to new connection
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "data": [status.dict() for status in self._service_status.values()]
                }))
                
                # Keep connection alive
                while True:
                    data = await websocket.receive_text()
                    # Echo back or handle client messages
                    await websocket.send_text(json.dumps({"type": "echo", "data": data}))
                    
            except WebSocketDisconnect:
                self._active_connections.remove(websocket)

        async def _notify_status_change(self, instance_id: int, status: str):
            """Notify all WebSocket clients of status change"""
            if instance_id in self._service_status:
                message = json.dumps({
                    "type": "status_change",
                    "instance_id": instance_id,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                for connection in self._active_connections:
                    try:
                        await connection.send_text(message)
                    except:
                        # Remove dead connections
                        self._active_connections.remove(connection)

    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.router
