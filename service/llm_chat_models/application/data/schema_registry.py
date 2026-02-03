import logging
import httpx
from typing import Dict, Any, Optional, List

from infrastructure.observability.scripts.observability_client import ObservabilityClient, trace_with_details
from ..config.credentials import ApicurioConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

obs = ObservabilityClient(service_name="schema-registry")
tracer = obs.tracer


class SchemaRegistry:
    def __init__(self):
        self.base_url = ApicurioConfig.BASE_URL
        self.api_version = ApicurioConfig.API_VERSION
        self.group_id = ApicurioConfig.GROUP_ID
        logger.info("event=schema_registry_init base_url=%s group_id=%s", self.base_url, self.group_id)

    def _get_api_url(self, path: str) -> str:
        return f"{self.base_url}/apis/registry/{self.api_version}{path}"

    @trace_with_details(tracer)
    async def register_schema(self, artifact_id: str, content: str, artifact_type: str = "JSON", description: Optional[str] = None) -> Dict[str, Any]:
        logger.info("event=register_schema artifact_id=%s type=%s", artifact_id, artifact_type)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts")
        headers = {
            "Content-Type": f"application/{artifact_type.lower()}",
            "X-Registry-ArtifactId": artifact_id,
            "X-Registry-ArtifactType": artifact_type
        }
        if description:
            headers["X-Registry-Description"] = description
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=content, headers=headers)
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("event=register_schema_success artifact_id=%s version=%s", artifact_id, result.get("version"))
                obs.increment_counter("schema_registry.register", 1, {"status": "success"})
                return result
            logger.error("event=register_schema_error artifact_id=%s status=%d body=%s", artifact_id, response.status_code, response.text)
            obs.increment_counter("schema_registry.register", 1, {"status": "error"})
            raise Exception(f"Failed to register schema: {response.status_code} - {response.text}")

    @trace_with_details(tracer)
    async def get_schema(self, artifact_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        logger.info("event=get_schema artifact_id=%s version=%s", artifact_id, version)
        if version:
            url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}/versions/{version}")
        else:
            url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                logger.info("event=get_schema_success artifact_id=%s", artifact_id)
                return {"content": response.text, "artifact_id": artifact_id}
            logger.error("event=get_schema_error artifact_id=%s status=%d", artifact_id, response.status_code)
            raise Exception(f"Schema not found: {artifact_id}")

    @trace_with_details(tracer)
    async def get_schema_metadata(self, artifact_id: str) -> Dict[str, Any]:
        logger.info("event=get_schema_metadata artifact_id=%s", artifact_id)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}/meta")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                result = response.json()
                logger.info("event=get_schema_metadata_success artifact_id=%s", artifact_id)
                return result
            logger.error("event=get_schema_metadata_error artifact_id=%s status=%d", artifact_id, response.status_code)
            raise Exception(f"Schema metadata not found: {artifact_id}")

    @trace_with_details(tracer)
    async def list_schemas(self) -> List[Dict[str, Any]]:
        logger.info("event=list_schemas group_id=%s", self.group_id)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                result = response.json()
                artifacts = result.get("artifacts", [])
                logger.info("event=list_schemas_success count=%d", len(artifacts))
                return artifacts
            logger.error("event=list_schemas_error status=%d", response.status_code)
            return []

    @trace_with_details(tracer)
    async def update_schema(self, artifact_id: str, content: str, artifact_type: str = "JSON") -> Dict[str, Any]:
        logger.info("event=update_schema artifact_id=%s", artifact_id)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}")
        headers = {
            "Content-Type": f"application/{artifact_type.lower()}"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(url, content=content, headers=headers)
            if response.status_code == 200:
                result = response.json()
                logger.info("event=update_schema_success artifact_id=%s version=%s", artifact_id, result.get("version"))
                obs.increment_counter("schema_registry.update", 1, {"status": "success"})
                return result
            logger.error("event=update_schema_error artifact_id=%s status=%d", artifact_id, response.status_code)
            obs.increment_counter("schema_registry.update", 1, {"status": "error"})
            raise Exception(f"Failed to update schema: {response.status_code} - {response.text}")

    @trace_with_details(tracer)
    async def delete_schema(self, artifact_id: str) -> bool:
        logger.info("event=delete_schema artifact_id=%s", artifact_id)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url)
            if response.status_code == 204:
                logger.info("event=delete_schema_success artifact_id=%s", artifact_id)
                obs.increment_counter("schema_registry.delete", 1, {"status": "success"})
                return True
            logger.error("event=delete_schema_error artifact_id=%s status=%d", artifact_id, response.status_code)
            obs.increment_counter("schema_registry.delete", 1, {"status": "error"})
            return False

    @trace_with_details(tracer)
    async def list_versions(self, artifact_id: str) -> List[Dict[str, Any]]:
        logger.info("event=list_versions artifact_id=%s", artifact_id)
        url = self._get_api_url(f"/groups/{self.group_id}/artifacts/{artifact_id}/versions")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                result = response.json()
                versions = result.get("versions", [])
                logger.info("event=list_versions_success artifact_id=%s count=%d", artifact_id, len(versions))
                return versions
            logger.error("event=list_versions_error artifact_id=%s status=%d", artifact_id, response.status_code)
            return []

    @trace_with_details(tracer)
    async def health_check(self) -> bool:
        logger.info("event=schema_registry_health_check")
        url = f"{self.base_url}/health/ready"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                healthy = response.status_code == 200
                logger.info("event=schema_registry_health_check_result healthy=%s", healthy)
                return healthy
        except Exception as e:
            logger.error("event=schema_registry_health_check_error error=%s", str(e))
            return False


schema_registry = SchemaRegistry()
