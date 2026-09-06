from typing import Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class HealthCheckSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    protocol: str = Field(default="http", alias="protocol")
    path: str = Field(default="/health", alias="path")
    interval: Optional[int] = Field(default=None, alias="interval")
    timeout: Optional[int] = Field(default=None, alias="timeout")
    success_threshold: Optional[int] = Field(default=None, alias="successThreshold")
    failure_threshold: Optional[int] = Field(default=None, alias="failureThreshold")

class ServiceInstanceModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="id")
    name: str = Field(..., alias="name")
    host: str = Field(..., alias="host")
    port: int = Field(..., alias="port")
    protocol: str = Field(default="http", alias="protocol")
    version: Optional[str] = Field(default=None, alias="version")
    weight: int = Field(default=100, alias="weight")
    status: int = Field(default=0, alias="status")
    health_check: HealthCheckSpec = Field(default_factory=HealthCheckSpec, alias="healthCheck")
    metadata: Dict[str, str] = Field(default_factory=dict, alias="metadata")
    registered_at: Optional[str] = Field(default=None, alias="registeredAt")
    last_heartbeat: Optional[str] = Field(default=None, alias="lastHeartbeat")

    @property
    def endpoint(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

class RegisterInstanceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="name")
    host: str = Field(..., alias="host")
    port: int = Field(..., alias="port")
    protocol: str = Field(default="http", alias="protocol")
    version: Optional[str] = Field(default=None, alias="version")
    weight: Optional[int] = Field(default=100, alias="weight")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, alias="metadata")
    health_check: HealthCheckSpec = Field(default_factory=HealthCheckSpec, alias="healthCheck")

class HeartbeatInstanceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="name")
    instance_id: str = Field(..., alias="instanceId")

class DeregisterInstanceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="name")
    instance_id: str = Field(..., alias="instanceId")

class ResolveServiceData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    service: str = Field(..., alias="service")
    endpoint: str = Field(..., alias="endpoint")
    instances: List[ServiceInstanceModel] = Field(default_factory=list, alias="instances")

class ApiMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: Optional[str] = Field(default=None, alias="requestId")
    correlation_id: Optional[str] = Field(default=None, alias="correlationId")
    causation_id: Optional[str] = Field(default=None, alias="causationId")
    timestamp: Optional[str] = Field(default=None, alias="timestamp")
    execution_time_ms: Optional[int] = Field(default=None, alias="executionTimeMs")

class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(default=True, alias="success")
    status_code: int = Field(default=200, alias="statusCode")
    data: Optional[T] = Field(default=None, alias="data")
    meta: Optional[ApiMeta] = Field(default=None, alias="meta")
