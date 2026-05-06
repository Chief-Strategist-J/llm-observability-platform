import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import requests
from requests import Response

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


class QdrantConnectionConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    host: str = Field("172.29.0.60")
    port: int = Field(6333)
    api_key: Optional[str] = Field("QdrantPassword123!")
    timeout: int = Field(30)
    verify_ssl: bool = Field(False)


class QdrantQueryResult(BaseModel):
    result: Any
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    operation_type: Optional[str] = None
    result_count: Optional[int] = None


obs = ObservabilityClient(service_name="qdrant-client")


def get_http_client(config: Optional[QdrantConnectionConfig] = None) -> requests.Session:
    if config is None:
        config = QdrantConnectionConfig()
    
    obs.log_info("Initializing Qdrant HTTP client", {
        "host": config.host,
        "port": config.port,
        "verify_ssl": config.verify_ssl
    })
    
    try:
        session = requests.Session()
        session.timeout = config.timeout
        session.verify = config.verify_ssl
        
        if config.api_key:
            session.headers.update({
                "api-key": config.api_key
            })
        
        obs.log_info("Qdrant HTTP client initialized successfully")
        return session
    
    except Exception as e:
        obs.log_error(f"Failed to initialize Qdrant HTTP client: {e}")
        raise


def get_base_url(config: Optional[QdrantConnectionConfig] = None) -> str:
    if config is None:
        config = QdrantConnectionConfig()
    
    protocol = "https" if config.verify_ssl else "http"
    return f"{protocol}://{config.host}:{config.port}"


def execute_request(
    session: requests.Session,
    method: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> QdrantQueryResult:
    start_time = datetime.now()
    
    try:
        base_url = get_base_url()
        url = f"{base_url}{endpoint}"
        
        if method.upper() == "GET":
            response = session.get(url, params=params)
        elif method.upper() == "POST":
            response = session.post(url, json=payload, params=params)
        elif method.upper() == "PUT":
            response = session.put(url, json=payload, params=params)
        elif method.upper() == "DELETE":
            response = session.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.status_code in [200, 201]:
            result = response.json()
            result_count = None
            
            # Extract result count based on operation type
            if "result" in result:
                if isinstance(result["result"], list):
                    result_count = len(result["result"])
                elif isinstance(result["result"], dict) and "points" in result["result"]:
                    result_count = len(result["result"]["points"])
            
            obs.log_info(f"Qdrant request executed successfully", {
                "method": method,
                "endpoint": endpoint,
                "execution_time_ms": execution_time_ms,
                "status_code": response.status_code,
                "result_count": result_count
            })
            
            return QdrantQueryResult(
                result=result,
                execution_time_ms=execution_time_ms,
                success=True,
                operation_type=method.upper(),
                result_count=result_count
            )
        
        else:
            error_message = f"HTTP {response.status_code}: {response.text}"
            obs.log_error(f"Qdrant request failed: {error_message}")
            
            return QdrantQueryResult(
                result=None,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=error_message,
                operation_type=method.upper()
            )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Qdrant request execution failed: {e}")
        
        return QdrantQueryResult(
            result=None,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e),
            operation_type=method.upper()
        )


def search_points(
    session: requests.Session,
    collection_name: str,
    query_vector: List[float],
    limit: int = 10,
    filter_params: Optional[Dict[str, Any]] = None,
    with_payload: bool = False,
    with_vector: bool = False
) -> QdrantQueryResult:
    payload = {
        "vector": query_vector,
        "limit": limit,
        "with_payload": with_payload,
        "with_vector": with_vector
    }
    
    if filter_params:
        payload["filter"] = filter_params
    
    return execute_request(
        session,
        "POST",
        f"/collections/{collection_name}/points/search",
        payload
    )


def scroll_points(
    session: requests.Session,
    collection_name: str,
    filter_params: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    with_payload: bool = False,
    with_vector: bool = False
) -> QdrantQueryResult:
    payload = {
        "limit": limit,
        "with_payload": with_payload,
        "with_vector": with_vector
    }
    
    if filter_params:
        payload["filter"] = filter_params
    
    return execute_request(
        session,
        "POST",
        f"/collections/{collection_name}/points/scroll",
        payload
    )


def count_points(
    session: requests.Session,
    collection_name: str,
    filter_params: Optional[Dict[str, Any]] = None
) -> QdrantQueryResult:
    payload = {}
    
    if filter_params:
        payload["filter"] = filter_params
    
    return execute_request(
        session,
        "POST",
        f"/collections/{collection_name}/points/count",
        payload
    )


def get_collection_info(session: requests.Session, collection_name: str) -> QdrantQueryResult:
    return execute_request(
        session,
        "GET",
        f"/collections/{collection_name}"
    )


def list_collections(session: requests.Session) -> QdrantQueryResult:
    return execute_request(
        session,
        "GET",
        "/collections"
    )


def get_cluster_info(session: requests.Session) -> QdrantQueryResult:
    return execute_request(
        session,
        "GET",
        "/cluster"
    )


def get_health_check(session: requests.Session) -> QdrantQueryResult:
    return execute_request(
        session,
        "GET",
        "/health"
    )


def get_metrics(session: requests.Session) -> QdrantQueryResult:
    return execute_request(
        session,
        "GET",
        "/metrics"
    )


def create_collection(
    session: requests.Session,
    collection_name: str,
    vector_size: int,
    distance: str = "Cosine"
) -> QdrantQueryResult:
    payload = {
        "vectors": {
            "size": vector_size,
            "distance": distance
        }
    }
    
    return execute_request(
        session,
        "PUT",
        f"/collections/{collection_name}",
        payload
    )


def delete_collection(session: requests.Session, collection_name: str) -> QdrantQueryResult:
    return execute_request(
        session,
        "DELETE",
        f"/collections/{collection_name}"
    )


def upsert_points(
    session: requests.Session,
    collection_name: str,
    points: List[Dict[str, Any]],
    wait: bool = False
) -> QdrantQueryResult:
    payload = {
        "points": points,
        "wait": wait
    }
    
    return execute_request(
        session,
        "PUT",
        f"/collections/{collection_name}/points",
        payload
    )


def delete_points(
    session: requests.Session,
    collection_name: str,
    points: Optional[List[str]] = None,
    filter_params: Optional[Dict[str, Any]] = None
) -> QdrantQueryResult:
    payload = {}
    
    if points:
        payload["points"] = points
    
    if filter_params:
        payload["filter"] = filter_params
    
    return execute_request(
        session,
        "POST",
        f"/collections/{collection_name}/points/delete",
        payload
    )


class QdrantTransactionManager:
    def __init__(self, session: requests.Session):
        self.session = session
        self.obs = ObservabilityClient(service_name="qdrant-transaction-manager")

    def execute_batch_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            results = []
            
            for operation in operations:
                method = operation["method"]
                endpoint = operation["endpoint"]
                payload = operation.get("payload")
                params = operation.get("params")
                
                result = execute_request(self.session, method, endpoint, payload, params)
                results.append(result)
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            success_count = len([r for r in results if r.success])
            
            self.obs.log_info(f"Qdrant batch operations executed", {
                "operations_count": len(operations),
                "success_count": success_count,
                "execution_time_ms": execution_time_ms
            })
            
            return {
                "success": success_count == len(operations),
                "results": results,
                "execution_time_ms": execution_time_ms,
                "operations_count": len(operations),
                "success_count": success_count
            }
        
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Qdrant batch operations failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "operations_count": len(operations)
            }


class QdrantCollectionManager:
    def __init__(self, session: requests.Session):
        self.session = session
        self.obs = ObservabilityClient(service_name="qdrant-collection-manager")

    def create_collection_with_config(
        self,
        collection_name: str,
        vector_config: Dict[str, Any],
        hnsw_config: Optional[Dict[str, Any]] = None,
        quantization_config: Optional[Dict[str, Any]] = None,
        on_disk: Optional[bool] = None
    ) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            payload = {
                "vectors": vector_config
            }
            
            if hnsw_config:
                payload["hnsw_config"] = hnsw_config
            
            if quantization_config:
                payload["quantization_config"] = quantization_config
            
            if on_disk is not None:
                payload["on_disk"] = on_disk
            
            result = execute_request(
                self.session,
                "PUT",
                f"/collections/{collection_name}",
                payload
            )
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            self.obs.log_info(f"Qdrant collection created", {
                "collection_name": collection_name,
                "execution_time_ms": execution_time_ms,
                "success": result.success
            })
            
            return {
                "success": result.success,
                "result": result.result,
                "execution_time_ms": execution_time_ms,
                "collection_name": collection_name
            }
        
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Qdrant collection creation failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "collection_name": collection_name
            }

    def get_collection_statistics(self, collection_name: str) -> Dict[str, Any]:
        try:
            # Get collection info
            collection_info = get_collection_info(self.session, collection_name)
            
            if not collection_info.success:
                return {"error": collection_info.error_message}
            
            # Get point count
            count_result = count_points(self.session, collection_name)
            
            # Get sample points to estimate data size
            scroll_result = scroll_points(self.session, collection_name, limit=1)
            
            stats = {
                "collection_info": collection_info.result,
                "point_count": count_result.result.get("result", {}).get("count", 0) if count_result.success else 0,
                "sample_point": scroll_result.result.get("result", {}).get("points", [None])[0] if scroll_result.success and scroll_result.result.get("result", {}).get("points") else None
            }
            
            return stats
        
        except Exception as e:
            self.obs.log_error(f"Failed to get collection statistics: {e}")
            return {"error": str(e)}
