import requests
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GrafanaClient")


class GrafanaClient:
    def __init__(
        self,
        grafana_url: str = "http://localhost:31001",
        username: str = "admin",
        password: str = "SuperSecret123!"
    ):
        self.grafana_url = grafana_url.rstrip("/")
        self.auth = (username, password)

    def _req(self, method: str, path: str, json: Any = None) -> Any:
        url = self.grafana_url + path
        try:
            logger.info(f"{method} {url}")
            response = requests.request(method, url, json=json, auth=self.auth, timeout=10)
            response.raise_for_status()
            logger.info(f"Success: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}

    def add_datasource(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._req("POST", "/api/datasources", payload)

    def update_datasource(self, datasource_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._req("PUT", f"/api/datasources/{datasource_id}", payload)

    def delete_datasource(self, datasource_id: int) -> Dict[str, Any]:
        return self._req("DELETE", f"/api/datasources/{datasource_id}")

    def get_all_datasources(self) -> List[Dict[str, Any]]:
        return self._req("GET", "/api/datasources")

    def get_datasource_by_name(self, name: str) -> Dict[str, Any]:
        return self._req("GET", f"/api/datasources/name/{name}")
